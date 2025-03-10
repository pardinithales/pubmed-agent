import asyncio
from typing import Dict, List, Optional, Tuple, Any

from app.services.pubmed_service import PubMedService
from app.models.schemas import PubMedSearchResult, QueryIteration
from app.utils.logger import get_logger

logger = get_logger(__name__)

class QueryEvaluator:
    """
    Serviço para avaliar e refinar consultas PubMed com base nos resultados obtidos.
    Implementa a lógica de avaliação da qualidade e iteração de refinamento.
    """
    
    def __init__(self, pubmed_service: PubMedService):
        """
        Inicializa o avaliador de consultas
        
        Args:
            pubmed_service: Instância do serviço PubMed para executar consultas
        """
        self.pubmed_service = pubmed_service
        
        # Palavras-chave indicativas de tipos de estudo específicos
        self.keywords = {
            "primary_studies": [
                "randomized", "trial", "cohort", "case-control", "observational",
                "cross-sectional", "longitudinal", "prospective", "retrospective"
            ],
            "systematic_reviews": [
                "systematic review", "meta-analysis", "systematic literature review",
                "evidence synthesis", "umbrella review"
            ]
        }
    
    async def refine_query(
        self, 
        initial_query: str, 
        max_iterations: int = 5
    ) -> Tuple[str, List[QueryIteration]]:
        """
        Executa o processo iterativo de refinamento da consulta PubMed
        
        Args:
            initial_query: Consulta inicial gerada a partir do texto PICOTT
            max_iterations: Número máximo de iterações de refinamento
            
        Returns:
            Tuple[str, List[QueryIteration]]: Melhor consulta encontrada e histórico de iterações
        """
        logger.info(f"Iniciando processo de refinamento. Consulta inicial: {initial_query}")
        
        current_query = initial_query
        iterations: List[QueryIteration] = []
        best_query = initial_query
        best_score = 0.0
        
        # Primeira iteração com a consulta inicial
        search_result = await self.pubmed_service.search(current_query)
        evaluation = self._evaluate_search_result(search_result)
        score = evaluation.get("overall_score", 0.0)
        
        # Registra a primeira iteração
        iterations.append(
            QueryIteration(
                iteration_number=1,
                query=current_query,
                result_count=search_result.total_count,
                evaluation=evaluation,
                refinement_reason=(
                    "Consulta inicial gerada a partir do texto PICOTT"
                )
            )
        )
        
        # Se a primeira consulta já é boa o suficiente, retorna
        if self._is_query_good_enough(evaluation):
            logger.info("Consulta inicial considerada boa o suficiente. Finalizando.")
            return current_query, iterations
        
        # Atualiza a melhor consulta se necessário
        if score > best_score:
            best_query = current_query
            best_score = score
        
        # Ciclo de refinamento iterativo
        for i in range(2, max_iterations + 1):
            logger.info(f"Iniciando iteração {i} de refinamento")
            
            # Gera uma consulta refinada baseada na avaliação anterior
            refined_query = await self._generate_refined_query(current_query, evaluation)
            
            # Se a consulta refinada for igual à anterior, interrompe o ciclo
            if refined_query == current_query:
                logger.info("Consulta refinada igual à anterior. Finalizando ciclo.")
                break
            
            # Executa a consulta refinada e avalia
            current_query = refined_query
            search_result = await self.pubmed_service.search(current_query)
            evaluation = self._evaluate_search_result(search_result)
            score = evaluation.get("overall_score", 0.0)
            
            # Registra esta iteração
            iterations.append(
                QueryIteration(
                    iteration_number=i,
                    query=current_query,
                    result_count=search_result.total_count,
                    evaluation=evaluation,
                    refinement_reason=self._get_refinement_reason(evaluation)
                )
            )
            
            # Atualiza a melhor consulta se esta for melhor
            if score > best_score:
                best_query = current_query
                best_score = score
            
            # Verifica se a consulta atual é boa o suficiente
            if self._is_query_good_enough(evaluation):
                logger.info(f"Consulta da iteração {i} considerada boa o suficiente. Finalizando.")
                break
        
        # Retorna a melhor consulta encontrada e o histórico de iterações
        logger.info(f"Processo de refinamento concluído. Melhor consulta: {best_query}")
        return best_query, iterations
    
    def _evaluate_search_result(self, result: PubMedSearchResult) -> Dict[str, Any]:
        """
        Avalia a qualidade da consulta baseada nos resultados da busca
        
        Args:
            result: Resultado da busca no PubMed
            
        Returns:
            Dict[str, Any]: Métricas de avaliação da consulta
        """
        # Número total de resultados
        total_count = result.total_count
        
        # Avalia se o número de resultados está na faixa ideal (100-500)
        count_score = self._calculate_count_score(total_count)
        
        # Analisa os títulos da amostra para detectar estudos primários e revisões
        primary_studies = 0
        systematic_reviews = 0
        
        if result.sample_titles:
            for title in result.sample_titles:
                title_lower = title.lower()
                
                # Verifica se o título contém palavras-chave de estudos primários
                if any(kw.lower() in title_lower for kw in self.keywords["primary_studies"]):
                    primary_studies += 1
                
                # Verifica se o título contém palavras-chave de revisões sistemáticas
                if any(kw.lower() in title_lower for kw in self.keywords["systematic_reviews"]):
                    systematic_reviews += 1
        
        # Calcula proporções se houver títulos na amostra
        sample_size = len(result.sample_titles) if result.sample_titles else 1
        primary_studies_ratio = primary_studies / sample_size
        systematic_reviews_ratio = systematic_reviews / sample_size
        
        # Relevância média (simplificada - uma implementação mais robusta usaria LLM)
        # Para este exemplo, consideramos uma relevância baseada nas proporções de estudos
        relevance_score = 0.7 * primary_studies_ratio + 0.3 * systematic_reviews_ratio
        
        # Pontuação geral ponderada
        overall_score = (
            0.5 * count_score +            # Peso para o número de resultados
            0.3 * primary_studies_ratio +  # Peso para estudos primários
            0.1 * systematic_reviews_ratio + # Peso para revisões sistemáticas
            0.1 * relevance_score          # Peso para relevância geral
        )
        
        # Identifica problemas na consulta
        issues = self._identify_issues(
            total_count, 
            primary_studies_ratio, 
            systematic_reviews_ratio
        )
        
        # Constrói e retorna o dicionário de avaliação
        return {
            "total_count": total_count,
            "count_score": count_score,
            "primary_studies_ratio": primary_studies_ratio,
            "systematic_reviews_ratio": systematic_reviews_ratio,
            "average_relevance": relevance_score,
            "overall_score": overall_score,
            "issues": issues
        }
    
    def _calculate_count_score(self, count: int) -> float:
        """
        Calcula uma pontuação baseada no número de resultados
        Faixa ideal: 100-500 artigos
        
        Args:
            count: Número total de resultados
            
        Returns:
            float: Pontuação entre 0.0 e 1.0
        """
        if 100 <= count <= 500:
            # Pontuação máxima na faixa ideal
            return 1.0
        elif count < 100:
            # Pontuação proporcional para consultas muito específicas
            return count / 100.0
        else:
            # Pontuação inversamente proporcional para consultas muito amplas
            return 500.0 / count if count > 0 else 0.0
    
    def _identify_issues(
        self, 
        count: int, 
        primary_ratio: float, 
        review_ratio: float
    ) -> str:
        """
        Identifica problemas na consulta atual para orientar o refinamento
        
        Args:
            count: Número total de resultados
            primary_ratio: Proporção de estudos primários
            review_ratio: Proporção de revisões sistemáticas
            
        Returns:
            str: Descrição dos problemas identificados
        """
        issues = []
        
        # Verifica o número de resultados
        if count < 20:
            issues.append("Consulta muito específica, poucos resultados encontrados")
        elif count < 100:
            issues.append("Consulta relativamente específica, considere ampliar os termos")
        elif count > 500:
            issues.append("Consulta muito ampla, considere restringir os termos")
        elif count > 1000:
            issues.append("Consulta extremamente ampla, necessita maior especificidade")
        
        # Verifica a proporção de estudos primários
        if primary_ratio < 0.2:
            issues.append("Baixa proporção de estudos primários")
        
        # Verifica a proporção de revisões sistemáticas
        if review_ratio < 0.1 and primary_ratio < 0.3:
            issues.append("Poucos estudos relevantes encontrados")
        
        # Retorna os problemas identificados ou uma mensagem padrão
        if issues:
            return "; ".join(issues)
        else:
            return "Nenhum problema específico identificado"
    
    def _is_query_good_enough(self, evaluation: Dict[str, Any]) -> bool:
        """
        Verifica se a consulta atual é considerada boa o suficiente
        
        Args:
            evaluation: Métricas de avaliação da consulta
            
        Returns:
            bool: True se a consulta for considerada boa o suficiente
        """
        # Critérios para uma consulta ser considerada boa o suficiente
        count_in_range = 100 <= evaluation.get("total_count", 0) <= 500
        good_primary_ratio = evaluation.get("primary_studies_ratio", 0) >= 0.3
        good_overall_score = evaluation.get("overall_score", 0) >= 0.7
        
        # Uma consulta é boa se estiver na faixa ideal de resultados
        # e tiver uma proporção adequada de estudos primários
        # e tiver uma pontuação geral boa
        return count_in_range and good_primary_ratio and good_overall_score
    
    def _get_refinement_reason(self, evaluation: Dict[str, Any]) -> str:
        """
        Gera uma explicação para a necessidade de refinamento
        
        Args:
            evaluation: Métricas de avaliação da consulta
            
        Returns:
            str: Explicação para o refinamento
        """
        # Pega os problemas identificados na avaliação
        issues = evaluation.get("issues", "")
        
        # Se não houver problemas específicos, usa uma mensagem genérica
        if not issues or issues == "Nenhum problema específico identificado":
            return "Refinamento para melhorar a qualidade geral da consulta"
        
        # Caso contrário, usa os problemas como razão para o refinamento
        return f"Refinamento necessário para corrigir: {issues}"
    
    async def _generate_refined_query(
        self,
        current_query: str,
        evaluation: Dict[str, Any]
    ) -> str:
        """
        Gera uma consulta refinada com base na avaliação atual
        Este método seria idealmente implementado com LLM para refinamento inteligente,
        mas nesta versão, usamos regras simples.
        
        Args:
            current_query: Consulta atual
            evaluation: Métricas de avaliação da consulta atual
            
        Returns:
            str: Consulta refinada
        """
        # Em uma implementação completa, este método chamaria o QueryGenerator
        # para gerar uma consulta refinada usando LLM
        # Por agora, simularemos algumas regras simples de refinamento
        
        # Obtém o número de resultados atual
        count = evaluation.get("total_count", 0)
        
        refined_query = current_query
        
        # Se a consulta for muito específica (poucos resultados)
        if count < 100:
            # Simplificamos a consulta removendo alguns qualificadores [tiab]
            refined_query = refined_query.replace("[tiab]", "", 1)
            
            # Adicionamos alternativas com OR para termos existentes
            # (Simplificação - em um sistema real, usaríamos LLM para esta tarefa)
            if "[tiab]" in refined_query and " OR " not in refined_query:
                sample_alternatives = {
                    "diabetes tipo 2": "DM2",
                    "hipertensão": "pressão alta",
                    "randomized": "randomised",
                    "trial": "clinical trial",
                    "metformina": "biguanida"
                }
                
                for term, alternative in sample_alternatives.items():
                    if term in refined_query and alternative not in refined_query:
                        refined_query = refined_query.replace(
                            f"{term}[tiab]",
                            f"({term}[tiab] OR {alternative}[tiab])"
                        )
                        break
        
        # Se a consulta for muito ampla (muitos resultados)
        elif count > 500:
            # Tornamos a consulta mais específica adicionando mais termos [tiab]
            if "[tiab]" in refined_query and refined_query.count("AND") < 3:
                refined_query += " AND (randomized[tiab] OR trial[tiab])"
            
            # Ou adicionamos filtros adicionais
            # (Simplificação - em um sistema real, usaríamos LLM para esta tarefa)
            elif refined_query.count("AND") >= 3 and "AND human[filter]" not in refined_query:
                refined_query += " AND human[filter]"
        
        # Retornamos a consulta refinada (ou a original se não houve alterações)
        return refined_query

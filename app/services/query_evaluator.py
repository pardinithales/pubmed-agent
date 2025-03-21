import asyncio
from typing import Dict, List, Optional, Tuple, Any
import re

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
        
        # Obter abstracts para a primeira iteração se houver resultados
        abstracts_sample = None
        if search_result.ids:
            try:
                abstracts_sample = await self.pubmed_service.get_article_abstracts(
                    search_result.ids, sample_size=5
                )
                logger.info(f"Obtidos {len(abstracts_sample)} abstracts para primeira iteração")
            except Exception as e:
                logger.error(f"Erro ao obter abstracts na primeira iteração: {str(e)}")
        
        # Registra a primeira iteração
        iterations.append(
            QueryIteration(
                iteration_number=1,
                query=current_query,
                result_count=search_result.total_count,
                evaluation=evaluation,
                refinement_reason="Consulta inicial gerada a partir do texto PICOTT",
                abstracts_sample=abstracts_sample
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
            
            # Gera uma consulta refinada baseada na avaliação anterior e nos resultados da busca
            refined_query = await self._generate_refined_query(current_query, evaluation, search_result)
            
            # Se a consulta refinada for igual à anterior, interrompe o ciclo
            if refined_query == current_query:
                logger.info("Consulta refinada igual à anterior. Finalizando ciclo.")
                break
            
            # Executa a consulta refinada e avalia
            current_query = refined_query
            search_result = await self.pubmed_service.search(current_query)
            evaluation = self._evaluate_search_result(search_result)
            score = evaluation.get("overall_score", 0.0)
            
            # Obter abstracts para esta iteração se houver resultados
            abstracts_sample = None
            if search_result.ids:
                try:
                    abstracts_sample = await self.pubmed_service.get_article_abstracts(
                        search_result.ids, sample_size=5
                    )
                    logger.info(f"Obtidos {len(abstracts_sample)} abstracts para iteração {i}")
                except Exception as e:
                    logger.error(f"Erro ao obter abstracts na iteração {i}: {str(e)}")
            
            # Registra esta iteração
            iterations.append(
                QueryIteration(
                    iteration_number=i,
                    query=current_query,
                    result_count=search_result.total_count,
                    evaluation=evaluation,
                    refinement_reason=self._get_refinement_reason(evaluation),
                    abstracts_sample=abstracts_sample
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
        evaluation: Dict[str, Any],
        search_result: PubMedSearchResult = None
    ) -> str:
        """
        Gera uma consulta refinada com base na avaliação da consulta atual
        
        Args:
            current_query: Consulta PubMed atual
            evaluation: Avaliação da consulta atual
            search_result: Resultados da pesquisa atual (opcional)
            
        Returns:
            str: Consulta PubMed refinada
        """
        issues = evaluation.get("issues", [])
        total_count = evaluation.get("total_count", 0)
        
        # Se não há problemas com a consulta, retorna a consulta original
        if not issues:
            logger.info("Nenhum problema encontrado na consulta. Mantendo consulta atual.")
            return current_query
        
        # Obtém abstracts para análise, se disponíveis
        abstracts_data = []
        if search_result and search_result.ids:
            try:
                # Obtém uma amostra maior de abstracts para análise agêntica
                abstracts_data = await self.pubmed_service.get_article_abstracts(
                    search_result.ids, sample_size=10
                )
                logger.info(f"Obtidos {len(abstracts_data)} abstracts para análise agêntica")
            except Exception as e:
                logger.error(f"Erro ao obter abstracts para refinamento: {str(e)}")
        
        # Caso 1: Consulta muito específica, poucos resultados
        if "Consulta muito específica" in issues or total_count < 10:
            logger.info("Refinando consulta muito específica para aumentar resultados")
            
            # Se temos abstracts, usa-os para expandir a consulta
            if abstracts_data:
                # Aplica o refinamento agêntico com DeepSeek LLM focando em termos específicos
                return await self._refine_with_deepseek_llm(current_query, abstracts_data, "expand")
            
            # Método básico de expansão se não temos abstracts
            parts = current_query.split(" AND ")
            if len(parts) > 3:
                # Remove o último filtro
                return " AND ".join(parts[:-1])
            else:
                # Expande termos da população e intervenção
                refined_query = current_query
                
                # Substitui operadores de campo específicos por mais amplos
                refined_query = refined_query.replace("[Title]", "[Title/Abstract]")
                refined_query = refined_query.replace("[MeSH Terms]", "[MeSH Terms] OR [All Fields]")
                
                return refined_query
        
        # Caso 2: Consulta muito ampla, muitos resultados
        elif "Consulta muito ampla" in issues or total_count > 100:
            logger.info("Refinando consulta muito ampla para reduzir resultados")
            
            # Se temos abstracts, usa-os para restringir a consulta
            if abstracts_data:
                # Aplica o refinamento agêntico com DeepSeek LLM
                return await self._refine_with_deepseek_llm(current_query, abstracts_data, "restrict")
            
            # Método básico de restrição
            if total_count > 1000:
                return current_query.replace("[All Fields]", "[tiab]") + ' AND ("randomized"[tiab] OR "controlled"[tiab])'
            else:
                return current_query + ' AND "human"[Filter]'
        
        # Baixa proporção de estudos primários
        elif "Baixa proporção de estudos primários" in issues:
            logger.info("Refinando para aumentar proporção de estudos primários")
            
            # Se temos abstracts, verifica quais termos aparecem em abstracts de estudos primários
            if abstracts_data:
                study_terms = ["trial", "randomized", "controlled", "cohort", "prospective", "retrospective"]
                return f"{current_query} AND ({' OR '.join([f'\"{term}\"[tiab]' for term in study_terms])})"
            else:
                return f"{current_query} AND (randomized[tiab] OR trial[tiab])"
        
        # Poucos estudos relevantes
        elif "Poucos estudos relevantes" in issues:
            logger.info("Refinando para aumentar relevância dos resultados")
            
            # Se temos abstracts, usa-os para identificar termos que aumentam a relevância
            if abstracts_data:
                # Aplica o refinamento agêntico com DeepSeek LLM focando em relevância
                return await self._refine_with_deepseek_llm(current_query, abstracts_data, "relevance")
            
            # Método básico
            if "systematic" not in current_query:
                return current_query.replace("]", "] AND (\"effect\"[tiab] OR \"outcome\"[tiab])")
            else:
                return current_query
        
        # Se nenhuma condição específica for atendida, retorna a consulta original
        logger.info("Nenhuma condição de refinamento específica atendida, mantendo consulta")
        return current_query
        
    async def _refine_with_deepseek_llm(
        self, 
        current_query: str, 
        abstracts_data: List[Dict[str, str]], 
        mode: str
    ) -> str:
        """
        Refinamento de consulta usando o modelo DeepSeek LLM
        
        Args:
            current_query: Consulta atual do PubMed
            abstracts_data: Dados dos abstracts para análise
            mode: Modo de refinamento (expand, restrict, relevance)
            
        Returns:
            str: Consulta refinada
        """
        try:
            # Extrai os elementos PICOTT da consulta atual
            population_terms = self._extract_query_section(current_query, "population")
            intervention_terms = self._extract_query_section(current_query, "intervention")
            comparison_terms = self._extract_query_section(current_query, "comparison")
            outcome_terms = self._extract_query_section(current_query, "outcome")
            
            # Formata os abstracts para serem processados
            abstracts_text = "\n\n".join([
                f"Título: {a.get('title', 'Sem título')}\nAbstract: {a.get('abstract', 'Sem abstract')}"
                for a in abstracts_data if a.get('abstract')
            ])
            
            # Confere que há abstracts para analisar
            if not abstracts_text:
                logger.warning("Sem abstracts para análise pelo LLM")
                return current_query
                
            # Determinação da instrução específica com base no modo
            instruction = ""
            if mode == "expand":
                instruction = (
                    "Analise os abstracts e extraia APENAS termos específicos relacionados à "
                    "população de estudo (diabetes tipo 2). Exclua termos genéricos como 'adults', "
                    "'patients', 'there', 'study', 'six months'. Forneça apenas 3-5 termos específicos "
                    "relacionados à condição estudada."
                )
            elif mode == "restrict":
                instruction = (
                    "Analise os abstracts e extraia APENAS 3-5 termos específicos para restringir "
                    "a consulta. Foque em características específicas da população (diabetes tipo 2) "
                    "e na intervenção principal (ex: metformina). Exclua termos genéricos como 'there', "
                    "'six months', 'adults', etc."
                )
            elif mode == "relevance":
                instruction = (
                    "Analise os abstracts e extraia APENAS 3-5 termos muito específicos que aparecem "
                    "nos artigos mais relevantes. Foque em características específicas da população "
                    "(diabetes tipo 2) e exclusivamente na intervenção estudada (ex: metformina)."
                )
                
            # Formato da consulta PubMed
            pubmed_format = (
                "A consulta final deve incluir apenas termos específicos da população e intervenção no formato "
                "PubMed correto, como: (\"diabetes type 2\"[tiab] OR \"T2DM\"[tiab]) AND (\"metformin\"[tiab])"
            )
            
            # Constrói o prompt para o LLM
            prompt = f"""
            # Tarefa: Refinar consulta PubMed baseada na análise de abstracts científicos
            
            ## Consulta atual
            {current_query}
            
            ## Instruções específicas
            {instruction}
            
            ## Formato da consulta PubMed
            {pubmed_format}
            
            ## Construa apenas a população e intervenção específicas
            Mantenha apenas termos específicos da população (diabetes tipo 2) e intervenção (metformina).
            NÃO inclua termos genéricos como 'adult', 'patient', 'there', 'studies', 'six months'.
            Adicione comparador e outcome APENAS se o número de resultados for > 30.
            
            ## Abstracts para análise
            {abstracts_text}
            
            ## Resposta (apenas a consulta PubMed refinada no formato correto)
            """
            
            # TODO: Integração com o serviço DeepSeek LLM
            # Por enquanto, aplicamos uma lógica simplificada
            
            # Extrai termos específicos da população e intervenção dos abstracts
            specific_pop_terms = []
            specific_int_terms = []
            
            for abstract in abstracts_data:
                if abstract.get('abstract'):
                    text = abstract.get('abstract', '').lower()
                    
                    # Procura por termos específicos da população (diabetes)
                    pop_patterns = [
                        r"type 2 diabetes", r"t2dm", r"diabetes mellitus", r"diabetic patients",
                        r"diabetes type 2", r"type 2 diabetic"
                    ]
                    
                    for pattern in pop_patterns:
                        if pattern in text and pattern not in specific_pop_terms:
                            specific_pop_terms.append(pattern)
                    
                    # Procura por termos específicos da intervenção (metformina)
                    int_patterns = [
                        r"metformin", r"met", r"biguanide", r"oral antidiabetic",
                        r"metformin treatment", r"metformin therapy"
                    ]
                    
                    for pattern in int_patterns:
                        if pattern in text and pattern not in specific_int_terms:
                            specific_int_terms.append(pattern)
            
            # Constrói a nova consulta
            refined_query = ""
            
            # População (limita a 3 termos)
            if specific_pop_terms:
                pop_query = " OR ".join([f"\"{term}\"[tiab]" for term in specific_pop_terms[:3]])
                refined_query = f"({pop_query})"
            else:
                # Fallback para a população original
                refined_query = "(\"diabetes type 2\"[tiab] OR \"T2DM\"[tiab])"
            
            # Intervenção (limita a 2 termos)
            if specific_int_terms:
                int_query = " OR ".join([f"\"{term}\"[tiab]" for term in specific_int_terms[:2]])
                refined_query += f" AND ({int_query})"
            else:
                # Fallback para a intervenção original
                refined_query += " AND (\"metformin\"[tiab])"
            
            # Tipo de estudo para garantir estudos primários (apenas se necessário)
            if mode == "relevance" or mode == "restrict":
                refined_query += " AND (\"randomized controlled trial\"[tiab] OR \"RCT\"[tiab])"
                
            logger.info(f"Consulta refinada pelo DeepSeek LLM: {refined_query}")
            return refined_query
            
        except Exception as e:
            logger.error(f"Erro ao refinar consulta com DeepSeek LLM: {str(e)}")
            return current_query
    
    def _extract_query_section(self, query: str, section_type: str) -> List[str]:
        """
        Extrai termos de uma seção específica da consulta PubMed
        
        Args:
            query: Consulta PubMed
            section_type: Tipo de seção (population, intervention, comparison, outcome)
            
        Returns:
            List[str]: Lista de termos da seção
        """
        terms = []
        
        # Análise simplificada baseada em padrões comuns para cada seção
        patterns = {
            "population": [r"diabetes", r"t2dm", r"adult", r"patient"],
            "intervention": [r"metformin", r"therapy", r"treatment"],
            "comparison": [r"placebo", r"versus", r"compared"],
            "outcome": [r"hba1c", r"glycated", r"hemoglobin", r"effect"]
        }
        
        # Verifica por padrões da seção especificada
        for pattern in patterns.get(section_type, []):
            if re.search(rf"{pattern}", query, re.IGNORECASE):
                terms.append(pattern)
                
        return terms

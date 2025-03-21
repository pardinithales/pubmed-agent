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
        search_result: Optional[PubMedSearchResult] = None
    ) -> str:
        """
        Gera uma consulta refinada com base na avaliação da consulta atual
        
        Args:
            current_query: Consulta atual
            evaluation: Avaliação da consulta atual
            search_result: Resultado da busca (opcional)
            
        Returns:
            str: Consulta refinada
        """
        issues = evaluation.get("issues", "")
        total_count = evaluation.get("total_count", 0)
        
        # Recupera abstracts dos artigos encontrados para análise e refinamento agêntico
        abstracts_data = []
        if search_result and search_result.ids:
            try:
                # Obtém abstracts de até 10 artigos aleatórios da consulta atual
                abstracts_data = await self.pubmed_service.get_article_abstracts(search_result.ids, sample_size=10)
                logger.info(f"Obtidos {len(abstracts_data)} abstracts para análise agêntica")
            except Exception as e:
                logger.error(f"Erro ao obter abstracts: {str(e)}")
        
        # Consulta muito específica (poucos resultados)
        if "muito específica" in issues or "poucos resultados" in issues:
            # Tenta generalizar a consulta
            logger.info("Refinando consulta muito específica para aumentar resultados")
            
            # Se temos abstracts, usa-os para identificar termos adicionais relevantes
            if abstracts_data:
                common_terms = self._extract_relevant_terms_from_abstracts(abstracts_data)
                logger.info(f"Termos relevantes extraídos dos abstracts: {common_terms}")
                
                # Adiciona termos alternativos/sinônimos à consulta
                parts = current_query.split(" AND ")
                refined_parts = []
                
                for part in parts:
                    # Se for uma parte fechada com parênteses, mantém a estrutura
                    if part.startswith("(") and part.endswith(")"):
                        term_part = part[1:-1]  # Remove os parênteses
                        terms = term_part.split(" OR ")
                        
                        # Adiciona novos termos relacionados dos abstracts
                        for term in common_terms[:3]:  # Limita a 3 termos novos
                            if term not in term_part:
                                terms.append(f'"{term}"[tiab]')
                        
                        refined_parts.append("(" + " OR ".join(terms) + ")")
                    else:
                        refined_parts.append(part)
                
                return " AND ".join(refined_parts)
            else:
                # Método básico: substitui os operadores mais restritivos
                return current_query.replace("[MeSH Terms]", "[MeSH Terms:noexp]").replace("[tiab]", "[All Fields]")
        
        # Consulta muito ampla (muitos resultados)
        elif "muito ampla" in issues or "restringir" in issues:
            logger.info("Refinando consulta muito ampla para reduzir resultados")
            
            # Se temos abstracts, usa-os para adicionar termos mais específicos
            if abstracts_data:
                specific_terms = self._extract_specific_terms_from_abstracts(abstracts_data)
                logger.info(f"Termos específicos extraídos: {specific_terms}")
                
                # Adiciona uma nova parte à consulta com termos específicos
                if specific_terms:
                    specific_filter = " OR ".join([f'"{term}"[tiab]' for term in specific_terms[:3]])
                    return f"{current_query} AND ({specific_filter})"
            
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
                relevance_terms = self._extract_relevant_terms_from_abstracts(abstracts_data)
                if relevance_terms:
                    refined_query = current_query
                    for term in relevance_terms[:2]:  # Limita a 2 termos
                        if term not in current_query:
                            refined_query += f' AND "{term}"[tiab]'
                    return refined_query
            
            # Método básico
            if "systematic" not in current_query:
                return current_query.replace("]", "] AND (\"effect\"[tiab] OR \"outcome\"[tiab])")
            else:
                return current_query
        
        # Se nenhuma condição específica for atendida, retorna a consulta original
        logger.info("Nenhuma condição de refinamento específica atendida, mantendo consulta")
        return current_query
    
    def _extract_relevant_terms_from_abstracts(self, abstracts_data: List[Dict[str, str]]) -> List[str]:
        """
        Extrai termos relevantes dos abstracts para expandir consultas
        
        Args:
            abstracts_data: Lista de dicionários com abstracts
            
        Returns:
            List[str]: Lista de termos relevantes
        """
        # Implementação básica - em produção, seria ideal usar NLP ou LLMs
        terms = []
        
        # Palavras a ignorar (stopwords e termos genéricos)
        stopwords = ["the", "and", "or", "in", "of", "to", "a", "an", "with", "for", 
                     "on", "at", "from", "by", "about", "as", "is", "was", "were", 
                     "be", "been", "being", "have", "has", "had", "do", "does", "did",
                     "but", "if", "because", "as", "until", "while", "however", "therefore"]
        
        # Conta ocorrências de termos nos abstracts
        term_count = {}
        
        for article in abstracts_data:
            if "abstract" in article and article["abstract"]:
                # Tokenização simples por espaços e pontuação
                abstract_text = article["abstract"].lower()
                words = abstract_text.replace(".", " ").replace(",", " ").replace(";", " ").replace(":", " ").split()
                
                # Remove stopwords e conta os termos
                for word in words:
                    word = word.strip()
                    if word and len(word) > 3 and word not in stopwords:
                        term_count[word] = term_count.get(word, 0) + 1
        
        # Retorna os termos mais frequentes
        sorted_terms = sorted(term_count.items(), key=lambda x: x[1], reverse=True)
        return [term for term, count in sorted_terms[:10] if count > 1]  # Retorna até 10 termos com ocorrência > 1
    
    def _extract_specific_terms_from_abstracts(self, abstracts_data: List[Dict[str, str]]) -> List[str]:
        """
        Extrai termos específicos dos abstracts para restringir consultas
        
        Args:
            abstracts_data: Lista de dicionários com abstracts
            
        Returns:
            List[str]: Lista de termos específicos
        """
        # Lista de marcadores de especificidade em abstracts
        specificity_markers = [
            "specifically", "particular", "unique", "distinct", "special",
            "precisely", "exactly", "exclusively", "only", "solely"
        ]
        
        # Procura por termos próximos a marcadores de especificidade
        specific_terms = []
        
        for article in abstracts_data:
            if "abstract" in article and article["abstract"]:
                abstract_text = article["abstract"].lower()
                
                # Verifica cada marcador de especificidade
                for marker in specificity_markers:
                    if marker in abstract_text:
                        # Encontra a posição do marcador
                        pos = abstract_text.find(marker)
                        
                        # Pega um trecho de 50 caracteres após o marcador
                        context = abstract_text[pos:pos+50] if pos+50 < len(abstract_text) else abstract_text[pos:]
                        
                        # Extrai o primeiro substantivo após o marcador (simplificado)
                        words = context.split()
                        if len(words) > 1:
                            # Adiciona a palavra após o marcador, se for longa o suficiente
                            candidate = words[1]
                            if len(candidate) > 3 and candidate not in specific_terms:
                                specific_terms.append(candidate)
        
        # Se não encontrou termos específicos pelos marcadores, usa os termos mais longos
        if not specific_terms:
            all_words = []
            for article in abstracts_data:
                if "abstract" in article and article["abstract"]:
                    words = article["abstract"].lower().split()
                    all_words.extend([word for word in words if len(word) > 6])  # Palavras longas tendem a ser mais específicas
            
            # Conta frequência
            word_count = {}
            for word in all_words:
                word_count[word] = word_count.get(word, 0) + 1
                
            # Seleciona termos específicos menos comuns
            specific_terms = [word for word, count in word_count.items() if count == 1][:5]
        
        return specific_terms

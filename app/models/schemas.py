from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class PICOTTQuery(BaseModel):
    """
    Modelo para representar uma consulta PICOTT do usuário
    """
    picott_text: str = Field(
        ..., 
        description="Texto descritivo da pergunta clínica no formato PICOTT (População, Intervenção, Comparação, Outcome, Tipo de estudo, Tempo)"
    )


class QueryIteration(BaseModel):
    """
    Modelo para representar uma iteração no processo de refinamento da consulta
    """
    iteration_number: int = Field(..., description="Número da iteração")
    query: str = Field(..., description="Consulta PubMed usada nesta iteração")
    result_count: int = Field(..., description="Número total de resultados obtidos")
    evaluation: Dict[str, Any] = Field(
        ..., 
        description="Métricas e avaliações da qualidade da consulta"
    )
    refinement_reason: Optional[str] = Field(
        None, 
        description="Razão para o refinamento da consulta na próxima iteração"
    )


class PubMedSearchResponse(BaseModel):
    """
    Modelo para representar a resposta da busca otimizada no PubMed
    """
    original_query: str = Field(..., description="Consulta original no formato PICOTT")
    best_pubmed_query: str = Field(..., description="Melhor consulta PubMed gerada pelo agente")
    iterations: List[QueryIteration] = Field(
        ..., 
        description="Lista das iterações realizadas no processo de refinamento"
    )
    

class PubMedSearchResult(BaseModel):
    """
    Modelo para representar resultados de uma busca no PubMed
    """
    query: str = Field(..., description="Consulta utilizada para a busca")
    total_count: int = Field(..., description="Número total de resultados encontrados")
    ids: List[str] = Field(..., description="Lista de IDs (PMIDs) dos artigos encontrados")
    sample_titles: Optional[List[str]] = Field(
        None, 
        description="Amostra de títulos dos primeiros resultados"
    )
    sample_types: Optional[List[str]] = Field(
        None, 
        description="Tipos de publicação dos artigos da amostra"
    )
    sample_years: Optional[List[str]] = Field(
        None, 
        description="Anos de publicação dos artigos da amostra"
    )


class ArticleMetadata(BaseModel):
    """
    Modelo para representar metadados de um artigo do PubMed
    """
    pmid: str = Field(..., description="ID do artigo no PubMed (PMID)")
    title: str = Field(..., description="Título do artigo")
    publication_type: List[str] = Field(..., description="Tipos de publicação")
    publication_year: str = Field(..., description="Ano de publicação")
    abstract: Optional[str] = Field(None, description="Resumo do artigo, se disponível")

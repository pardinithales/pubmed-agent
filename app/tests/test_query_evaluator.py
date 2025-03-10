import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from app.services.query_evaluator import QueryEvaluator
from app.models.schemas import PubMedSearchResult, PubMedArticle


@pytest.fixture
def query_evaluator():
    """Fixture para criar uma instância do avaliador de consultas para testes"""
    return QueryEvaluator()


@pytest.mark.asyncio
async def test_evaluate_query_simple(query_evaluator):
    """Teste simplificado para o avaliador de consultas"""
    
    # Cria um resultado de busca simples
    search_result = PubMedSearchResult(
        query="diabetes tipo 2 AND metformina AND HbA1c",
        total_count=25,
        ids=["1", "2"],
        articles=[
            PubMedArticle(
                id="1",
                title="Estudo sobre diabetes",
                abstract="Resumo do estudo...",
                authors=["Autor 1"],
                journal="Diabetes Care",
                publication_date="2023",
                article_type="Randomized Controlled Trial",
                url="https://pubmed.ncbi.nlm.nih.gov/1/"
            ),
            PubMedArticle(
                id="2",
                title="Outro estudo",
                abstract="Outro resumo...",
                authors=["Autor 2"],
                journal="Diabetes Journal",
                publication_date="2022",
                article_type="Clinical Trial",
                url="https://pubmed.ncbi.nlm.nih.gov/2/"
            )
        ]
    )
    
    # Mock da função de análise de relevância
    mock_relevance = {
        "article_1": {"relevance_score": 0.9, "reasoning": "Relevante"},
        "article_2": {"relevance_score": 0.8, "reasoning": "Relevante"}
    }
    
    # Patch do método interno
    with patch.object(QueryEvaluator, '_analyze_relevance', new=AsyncMock(return_value=mock_relevance)):
        # Executa a avaliação
        result = await query_evaluator.evaluate_query(search_result)
        
        # Verificações básicas
        assert isinstance(result, dict)
        assert "total_count" in result
        assert result["total_count"] == 25
        assert "average_relevance" in result
        assert result["average_relevance"] > 0.8
        assert "needs_refinement" in result


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

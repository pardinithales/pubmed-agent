import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import PubMedSearchResult, PubMedArticle, SearchQuery


@pytest.fixture
def client():
    """Fixture para criar um cliente de teste para a API FastAPI"""
    return TestClient(app)


def test_root_endpoint(client):
    """Testa o endpoint raiz da API"""
    response = client.get("/")
    assert response.status_code == 200
    assert "mensagem" in response.json()
    assert "documentacao" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "online"


def test_search_endpoint_validation():
    """Testa a validação do endpoint de busca"""
    client = TestClient(app)
    
    # Teste com corpo vazio
    response = client.post("/api/search", json={})
    assert response.status_code == 422  # Erro de validação
    
    # Teste com texto PICOTT vazio
    response = client.post("/api/search", json={"picott_text": ""})
    assert response.status_code == 422  # Erro de validação


@pytest.mark.asyncio
async def test_search_endpoint_success():
    """
    Testa o fluxo completo do endpoint de busca com mocks para componentes externos
    """
    # Mock para QueryGenerator.generate_initial_query
    async def mock_generate_initial_query(self, picott_text):
        return "diabetes tipo 2[tiab] AND metformina[tiab] AND HbA1c[tiab] AND randomized controlled trial[pt]"
    
    # Mock para PubMedService.search
    async def mock_search(self, query):
        return PubMedSearchResult(
            query=query,
            total_count=15,
            ids=["1", "2", "3"],
            articles=[
                PubMedArticle(
                    id="1",
                    title="Estudo de metformina em diabetes tipo 2",
                    abstract="Abstract do estudo...",
                    authors=["Autor AB", "Autor CD"],
                    journal="Diabetes Care",
                    publication_date="2023",
                    article_type="Randomized Controlled Trial",
                    url="https://pubmed.ncbi.nlm.nih.gov/1/"
                ),
                PubMedArticle(
                    id="2",
                    title="Outro estudo relevante",
                    abstract="Outro abstract...",
                    authors=["Pesquisador EF"],
                    journal="Journal of Diabetes",
                    publication_date="2022",
                    article_type="Clinical Trial",
                    url="https://pubmed.ncbi.nlm.nih.gov/2/"
                ),
                PubMedArticle(
                    id="3",
                    title="Mais um estudo",
                    abstract="Mais um abstract...",
                    authors=["Cientista GH"],
                    journal="Diabetes Research",
                    publication_date="2021",
                    article_type="Randomized Controlled Trial",
                    url="https://pubmed.ncbi.nlm.nih.gov/3/"
                )
            ]
        )
    
    # Mock para QueryEvaluator.evaluate_query
    async def mock_evaluate_query(self, search_result):
        return {
            "total_count": search_result.total_count,
            "count_score": 0.75,
            "primary_studies_ratio": 0.67,
            "systematic_reviews_ratio": 0.0,
            "average_relevance": 0.85,
            "overall_score": 0.76,
            "issues": "",
            "needs_refinement": False
        }
    
    # Mock para QueryGenerator.refine_query
    async def mock_refine_query(self, current_query, evaluation_results):
        return "(diabetes tipo 2[tiab] OR T2DM[tiab]) AND (metformina[tiab] OR biguanida[tiab]) AND HbA1c[tiab] AND (randomized controlled trial[pt] OR RCT[tiab])"
    
    # Aplica os patches
    with patch('app.services.query_generator.QueryGenerator.generate_initial_query', new=mock_generate_initial_query), \
         patch('app.services.pubmed_service.PubMedService.search', new=mock_search), \
         patch('app.services.query_evaluator.QueryEvaluator.evaluate_query', new=mock_evaluate_query), \
         patch('app.services.query_generator.QueryGenerator.refine_query', new=mock_refine_query):
        
        # Cria o cliente e faz a requisição
        client = TestClient(app)
        response = client.post("/api/search", json={
            "picott_text": "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
        })
        
        # Verificações
        assert response.status_code == 200
        data = response.json()
        assert "original_query" in data
        assert "best_pubmed_query" in data
        assert "iterations" in data
        assert len(data["iterations"]) > 0
        
        # Verifica a consulta final
        assert "diabetes tipo 2" in data["best_pubmed_query"]
        assert "metformina" in data["best_pubmed_query"]
        assert "HbA1c" in data["best_pubmed_query"]


@pytest.mark.asyncio
async def test_search_endpoint_with_refinement():
    """
    Testa o fluxo completo do endpoint de busca com refinamento de consulta
    """
    # Contador para controlar o comportamento do mock de avaliação
    evaluation_calls = 0
    
    # Mock para QueryGenerator.generate_initial_query
    async def mock_generate_initial_query(self, picott_text):
        return "diabetes[tiab] AND metformina[tiab]"  # Consulta inicial muito simples
    
    # Mock para PubMedService.search
    async def mock_search(self, query):
        # Retorna diferentes resultados dependendo da consulta
        if "OR" not in query:
            # Primeira consulta (muito ampla)
            return PubMedSearchResult(
                query=query,
                total_count=500,
                ids=["1", "2", "3"],
                articles=[PubMedArticle(
                    id=str(i),
                    title=f"Estudo {i}",
                    abstract=f"Abstract {i}...",
                    authors=[f"Autor{i}"],
                    journal="Journal",
                    publication_date="2023",
                    article_type="Research",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{i}/"
                ) for i in range(1, 4)]
            )
        else:
            # Consulta refinada (melhores resultados)
            return PubMedSearchResult(
                query=query,
                total_count=25,
                ids=["10", "20", "30"],
                articles=[PubMedArticle(
                    id=str(i*10),
                    title=f"Bom estudo {i}",
                    abstract=f"Bom abstract {i}...",
                    authors=[f"BomAutor{i}"],
                    journal="Good Journal",
                    publication_date="2023",
                    article_type="Randomized Controlled Trial",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{i*10}/"
                ) for i in range(1, 4)]
            )
    
    # Mock para QueryEvaluator.evaluate_query
    async def mock_evaluate_query(self, search_result):
        nonlocal evaluation_calls
        evaluation_calls += 1
        
        if evaluation_calls == 1:
            # Primeira avaliação (precisa de refinamento)
            return {
                "total_count": search_result.total_count,
                "count_score": 0.2,
                "primary_studies_ratio": 0.3,
                "systematic_reviews_ratio": 0.0,
                "average_relevance": 0.4,
                "overall_score": 0.3,
                "issues": "Consulta muito ampla, muitos resultados",
                "needs_refinement": True
            }
        else:
            # Segunda avaliação (boa)
            return {
                "total_count": search_result.total_count,
                "count_score": 0.8,
                "primary_studies_ratio": 0.9,
                "systematic_reviews_ratio": 0.0,
                "average_relevance": 0.9,
                "overall_score": 0.85,
                "issues": "",
                "needs_refinement": False
            }
    
    # Mock para QueryGenerator.refine_query
    async def mock_refine_query(self, current_query, evaluation_results):
        return "(diabetes tipo 2[tiab] OR T2DM[tiab]) AND (metformina[tiab] OR biguanida[tiab]) AND HbA1c[tiab] AND randomized controlled trial[pt]"
    
    # Aplica os patches
    with patch('app.services.query_generator.QueryGenerator.generate_initial_query', new=mock_generate_initial_query), \
         patch('app.services.pubmed_service.PubMedService.search', new=mock_search), \
         patch('app.services.query_evaluator.QueryEvaluator.evaluate_query', new=mock_evaluate_query), \
         patch('app.services.query_generator.QueryGenerator.refine_query', new=mock_refine_query):
        
        # Cria o cliente e faz a requisição
        client = TestClient(app)
        response = client.post("/api/search", json={
            "picott_text": "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
        })
        
        # Verificações
        assert response.status_code == 200
        data = response.json()
        assert "original_query" in data
        assert "best_pubmed_query" in data
        assert "iterations" in data
        assert len(data["iterations"]) == 2  # Deve ter duas iterações
        
        # Verifica a consulta final
        assert "diabetes tipo 2" in data["best_pubmed_query"]
        assert "T2DM" in data["best_pubmed_query"]  # Deve ter alternativas
        assert "metformina" in data["best_pubmed_query"]
        assert "randomized controlled trial" in data["best_pubmed_query"]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

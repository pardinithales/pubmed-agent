import pytest
import httpx
import asyncio
from unittest.mock import patch, MagicMock

from app.services.pubmed_service import PubMedService
from app.models.schemas import PubMedSearchResult


@pytest.fixture
def pubmed_service():
    """Fixture para criar uma instância do serviço PubMed para testes"""
    return PubMedService()


@pytest.mark.asyncio
async def test_search_success(pubmed_service):
    """Testa a busca bem-sucedida no PubMed"""
    
    # XML de resposta simulada do PubMed
    mock_xml = """
    <eSearchResult>
        <Count>42</Count>
        <RetMax>20</RetMax>
        <IdList>
            <Id>12345678</Id>
            <Id>23456789</Id>
            <Id>34567890</Id>
        </IdList>
    </eSearchResult>
    """
    
    # Mock da resposta HTTP
    mock_response = MagicMock()
    mock_response.text = mock_xml
    mock_response.raise_for_status = MagicMock()
    
    # Mock do cliente httpx para simular a requisição à API
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        with patch.object(pubmed_service, '_get_articles_metadata', return_value=[]):
            result = await pubmed_service.search("test query")
    
    # Verificações
    assert isinstance(result, PubMedSearchResult)
    assert result.total_count == 42
    assert len(result.ids) == 3
    assert result.ids[0] == "12345678"


@pytest.mark.asyncio
async def test_search_no_results(pubmed_service):
    """Testa a busca no PubMed sem resultados"""
    
    # XML de resposta simulada do PubMed sem resultados
    mock_xml = """
    <eSearchResult>
        <Count>0</Count>
        <RetMax>0</RetMax>
        <IdList>
        </IdList>
    </eSearchResult>
    """
    
    # Mock da resposta HTTP
    mock_response = MagicMock()
    mock_response.text = mock_xml
    mock_response.raise_for_status = MagicMock()
    
    # Mock do cliente httpx para simular a requisição à API
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        result = await pubmed_service.search("nonexistent query")
    
    # Verificações
    assert isinstance(result, PubMedSearchResult)
    assert result.total_count == 0
    assert len(result.ids) == 0


@pytest.mark.asyncio
async def test_search_api_error(pubmed_service):
    """Testa o comportamento quando a API do PubMed retorna erro"""
    
    # Simula um erro HTTP
    with patch('httpx.AsyncClient.get', side_effect=httpx.HTTPStatusError("API Error", request=MagicMock(), response=MagicMock())):
        with pytest.raises(Exception):
            await pubmed_service.search("test query")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

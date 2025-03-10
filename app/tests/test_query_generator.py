import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.query_generator import QueryGenerator


@pytest.fixture
def query_generator():
    """Fixture para criar uma instância do gerador de consultas para testes"""
    return QueryGenerator()


@pytest.mark.asyncio
async def test_generate_initial_query_with_deepseek(query_generator):
    """Testa a geração de consultas iniciais usando DeepSeek"""
    
    # Mock da resposta da API DeepSeek
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "\"diabetes tipo 2\"[tiab] AND \"metformina\"[tiab] AND \"HbA1c\"[tiab] AND \"randomized controlled trial\"[tiab] AND \"6 months\"[tiab]"
    
    # Mock do cliente OpenAI
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Patch do método de geração com DeepSeek diretamente
    with patch('app.services.query_generator.QueryGenerator._generate_with_deepseek', 
               AsyncMock(return_value="\"diabetes tipo 2\"[tiab] AND \"metformina\"[tiab] AND \"HbA1c\"[tiab] AND \"randomized controlled trial\"[tiab] AND \"6 months\"[tiab]")):
        
        query_generator.deepseek_api_key = "test_key"  # Garante que usamos DeepSeek
        query_generator.openai_api_key = None  # Desativa OpenAI
        
        # Consulta PICOTT de exemplo
        picott_text = "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
        
        result = await query_generator.generate_initial_query(picott_text)
        
        # Verificações
        assert isinstance(result, str)
        assert "diabetes tipo 2" in result
        assert "metformina" in result
        assert "HbA1c" in result
        assert "randomized controlled trial" in result
        assert "6 months" in result
        assert "[tiab]" in result


@pytest.mark.asyncio
async def test_generate_initial_query_with_openai(query_generator):
    """Testa a geração de consultas iniciais usando OpenAI como fallback"""
    
    # Patch do método de geração com OpenAI diretamente
    with patch('app.services.query_generator.QueryGenerator._generate_with_openai', 
               AsyncMock(return_value="(\"diabetes mellitus tipo 2\"[tiab] OR \"DM2\"[tiab]) AND (\"metformina\"[tiab] OR \"biguanida\"[tiab]) AND \"HbA1c\"[tiab] AND \"randomized\"[tiab]")):
        
        query_generator.deepseek_api_key = None  # Desativa DeepSeek
        query_generator.openai_api_key = "test_key"  # Garante que usamos OpenAI
        
        # Consulta PICOTT de exemplo
        picott_text = "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
        
        result = await query_generator.generate_initial_query(picott_text)
        
        # Verificações
        assert isinstance(result, str)
        assert "diabetes mellitus tipo 2" in result or "DM2" in result
        assert "metformina" in result or "biguanida" in result
        assert "HbA1c" in result
        assert "randomized" in result
        assert "[tiab]" in result


@pytest.mark.asyncio
async def test_refine_query(query_generator):
    """Testa o refinamento de consultas"""
    
    # Patch do método de refinamento diretamente
    with patch('app.services.query_generator.QueryGenerator._generate_with_deepseek', 
               AsyncMock(return_value="(\"diabetes tipo 2\"[tiab] OR \"DM2\"[tiab]) AND (\"metformina\"[tiab] OR \"biguanida\"[tiab]) AND \"HbA1c\"[tiab] AND (\"randomized controlled trial\"[tiab] OR \"RCT\"[tiab]) AND \"6 months\"[tiab]")):
        
        query_generator.deepseek_api_key = "test_key"  # Garante que usamos DeepSeek
        query_generator.openai_api_key = None  # Desativa OpenAI
        
        # Consulta atual e avaliação para refinamento
        current_query = "\"diabetes tipo 2\"[tiab] AND \"metformina\"[tiab] AND \"HbA1c\"[tiab] AND \"randomized controlled trial\"[tiab] AND \"6 months\"[tiab]"
        evaluation_results = {
            "total_count": 12,
            "count_score": 0.12,
            "primary_studies_ratio": 0.8,
            "systematic_reviews_ratio": 0.0,
            "average_relevance": 0.56,
            "overall_score": 0.34,
            "issues": "Consulta muito específica, poucos resultados encontrados",
            "needs_refinement": True
        }
        
        result = await query_generator.refine_query(current_query, evaluation_results)
        
        # Verificações
        assert isinstance(result, str)
        assert "diabetes tipo 2" in result
        assert "metformina" in result
        assert "HbA1c" in result
        assert "randomized controlled trial" in result or "RCT" in result
        assert "6 months" in result
        assert "OR" in result  # Deve ter adicionado alternativas
        assert "[tiab]" in result


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

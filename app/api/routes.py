from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import PICOTTQuery, PubMedSearchResponse
from app.services.pubmed_service import PubMedService
from app.services.query_generator import QueryGenerator
from app.services.query_evaluator import QueryEvaluator

router = APIRouter()

@router.post("/search", response_model=PubMedSearchResponse, status_code=status.HTTP_200_OK)
async def search_pubmed(query: PICOTTQuery):
    """
    Processa uma consulta PICOTT e retorna a melhor query otimizada para o PubMed.
    
    A rota implementa o fluxo completo do agente:
    1. Transforma o objetivo PICOTT em consulta inicial
    2. Avalia e refina a consulta iterativamente
    3. Retorna a melhor consulta encontrada
    """
    try:
        # Inicializa o gerador de consultas
        query_generator = QueryGenerator()
        
        # Gera a consulta inicial com base nos elementos PICOTT
        initial_query = await query_generator.generate_initial_query(query.picott_text)
        
        # Inicializa o serviço PubMed para executar as consultas
        pubmed_service = PubMedService()
        
        # Inicializa o avaliador de consultas
        query_evaluator = QueryEvaluator(pubmed_service)
        
        # Executa o processo de refinamento iterativo
        best_query, iterations = await query_evaluator.refine_query(
            initial_query=initial_query,
            max_iterations=5
        )
        
        # Prepara e retorna a resposta
        return PubMedSearchResponse(
            original_query=query.picott_text,
            best_pubmed_query=best_query,
            iterations=iterations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar a consulta: {str(e)}"
        )

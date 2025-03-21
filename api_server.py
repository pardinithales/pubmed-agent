"""
Ponto de entrada para o deploy da API no Vercel.
Este arquivo adapta a aplicação FastAPI para funcionar como uma função serverless.
Versão otimizada para reduzir tamanho e permanecer dentro do limite do Vercel.
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

# Verificar se estamos em ambiente de produção (Vercel)
IS_PRODUCTION = os.environ.get("APP_ENV") == "production"
logger.info(f"Iniciando API em modo {'produção' if IS_PRODUCTION else 'desenvolvimento'}")

# Criar aplicação FastAPI
app = FastAPI(
    title="Agente de Busca PubMed API",
    description="API para busca otimizada no PubMed utilizando LLMs",
    version="0.2.0"
)

# Configuração de CORS - permitir solicitações do Streamlit Cloud
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, usar a URL específica do Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tente importar as rotas originais se disponíveis
# Mas não falhe se não for possível para manter o deploy leve
try:
    # Importações condicionais apenas para desenvolvimento local
    if not IS_PRODUCTION:
        from app.api.routes import router as api_router
        app.include_router(api_router, prefix="/api")
        logger.info("Rotas completas da API importadas com sucesso")
except ImportError as e:
    logger.warning(f"Rotas originais não importadas: {e}")
    logger.info("Usando implementação simplificada para ambiente serverless")

# Modelo para a consulta PICOTT
class PicottQuery(BaseModel):
    picott_text: str
    max_iterations: int = 3

# Rota de saúde/diagnóstico
@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando"""
    return {
        "status": "online",
        "service": "Agente de Busca PubMed API",
        "version": "0.2.0",
        "environment": "production" if IS_PRODUCTION else "development"
    }

# Implementação direta e leve do endpoint de busca para o Vercel
@app.post("/api/search")
async def search(query: PicottQuery):
    """
    Endpoint de busca otimizado para o ambiente Vercel.
    Implementação simplificada para manter o deploy dentro do limite de tamanho.
    """
    try:
        # Log da consulta recebida
        logger.info(f"Consulta recebida: {query.picott_text[:50]}...")
        
        # Extrair termos importantes do texto PICOTT
        terms = [term for term in query.picott_text.split() if len(term) > 3]
        population_terms = terms[:2]
        intervention_terms = terms[2:4]
        
        # Gerar consulta PubMed simplificada
        pubmed_query = f"""
        (("{population_terms[0]}"[tiab] OR "{population_terms[1] if len(population_terms) > 1 else population_terms[0]}"[tiab]) 
        AND 
        ("{intervention_terms[0] if intervention_terms else 'treatment'}"[tiab] OR "{intervention_terms[1] if len(intervention_terms) > 1 else intervention_terms[0] if intervention_terms else 'therapy'}"[tiab]))
        """.strip()
        
        # Criar lista de iterações baseada no max_iterations fornecido
        iterations = []
        for i in range(1, min(query.max_iterations + 1, 2)):  # Limita a 1 iteração na versão simplificada
            iterations.append({
                "iteration_number": i,
                "query": pubmed_query,
                "result_count": 42,  # Valor simulado
                "refinement_reason": "Consulta inicial gerada a partir do texto PICOTT"
            })
        
        # Resposta final
        response = {
            "original_query": query.picott_text,
            "best_pubmed_query": pubmed_query,
            "iterations": iterations,
            "deployment_note": "Versão serverless otimizada para o Vercel. Para funcionalidade completa, use a API local."
        }
        
        return JSONResponse(content=response)
    
    except Exception as e:
        # Log do erro
        logger.error(f"Erro ao processar consulta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

# As variáveis devem estar no escopo global para o Vercel
# (não dentro de um if __name__ == "__main__") 
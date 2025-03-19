"""
Ponto de entrada para o deploy da API no Vercel.
Este arquivo adapta a aplicação FastAPI para funcionar como uma função serverless.
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

# Importações condicionais - importamos diretamente apenas o necessário
# para evitar problemas no ambiente serverless
try:
    # Em produção (Vercel), importe apenas o necessário
    from app.api.routes import router as api_router
    logger.info("Rotas da API importadas com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar rotas da API: {e}")
    # Implementação de fallback para garantir que a API inicie mesmo com erros
    api_router = None

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

# Usar as rotas da API se disponíveis
if api_router:
    app.include_router(api_router, prefix="/api")

# Modelo para a consulta PICOTT
class PicottQuery(BaseModel):
    picott_text: str

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

# Rota de fallback para /api/search caso haja problemas com as rotas importadas
@app.post("/api/search")
async def search_fallback(query: PicottQuery):
    """Endpoint de fallback para busca caso as rotas principais falhem"""
    if api_router:
        # Retornar erro para forçar o uso da rota correta do api_router
        raise HTTPException(status_code=404, detail="Use /api/search endpoint")
    
    # Implementação básica de fallback
    logger.warning("Usando implementação de fallback para /api/search")
    return JSONResponse({
        "original_query": query.picott_text,
        "best_pubmed_query": f'"{query.picott_text}"[Title/Abstract]',
        "iterations": [
            {
                "iteration_number": 1,
                "query": f'"{query.picott_text}"[Title/Abstract]',
                "result_count": 0,
                "refinement_reason": "Consulta inicial (fallback)"
            }
        ],
        "error": "Implementação de fallback - configuração completa indisponível"
    })

# Isso é importante para o Vercel
# Usamos a variável app diretamente como handler da função serverless 
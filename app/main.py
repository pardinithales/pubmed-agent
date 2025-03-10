import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="Agente de Busca PubMed",
    description="API para busca otimizada no PubMed utilizando LLMs",
    version="0.1.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão das rotas da API
app.include_router(api_router, prefix="/api")

# Rota raiz
@app.get("/")
async def root():
    return {
        "mensagem": "Bem-vindo ao Agente de Busca Otimizada para PubMed",
        "documentacao": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

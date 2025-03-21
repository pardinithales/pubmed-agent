#!/bin/bash

# Script para atualizar o serviço PubMed API no servidor Ubuntu
echo "Atualizando o código do PubMed Search API..."

# Navegar para o diretório do projeto
cd /root/pubmed_search

# Atualizar o código do repositório git (opcional, caso esteja usando git)
# git pull origin main

# Backup do arquivo de rotas atual
cp app/api/routes.py app/api/routes.py.bak
echo "Backup criado: app/api/routes.py.bak"

# Atualizar o arquivo de rotas para usar max_iterations do usuário
cat > app/api/routes.py << 'EOL'
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
            max_iterations=query.max_iterations
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
EOL
echo "Arquivo app/api/routes.py atualizado."

# Atualizar o arquivo de serviço do systemd
cat > /etc/systemd/system/pubmed_api.service << 'EOL'
[Unit]
Description=PubMed Search API Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/pubmed_search
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
Environment=PYTHONPATH=/root/pubmed_search
Environment=APP_ENV=production
Environment=MAX_ITERATIONS=5

[Install]
WantedBy=multi-user.target
EOL
echo "Arquivo de serviço systemd atualizado."

# Recarregar configuração do systemd
systemctl daemon-reload
echo "Configuração do systemd recarregada."

# Reiniciar o serviço
systemctl restart pubmed_api
echo "Serviço pubmed_api reiniciado."

# Verificar status do serviço
systemctl status pubmed_api
echo "Atualização concluída!" 
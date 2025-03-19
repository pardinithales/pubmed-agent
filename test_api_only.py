import asyncio
import httpx
import json
import time
import sys
import os
import importlib
import subprocess
from pathlib import Path

# Obter o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

# Configurar tempo de espera máximo para testes
MAX_WAIT_TIME = 30  # segundos

def check_and_install_dependencies():
    """Verifica e instala dependências faltantes do projeto."""
    print("Verificando dependências...")
    
    # Lista de dependências críticas para verificar
    critical_deps = [
        "httpx", "fastapi", "uvicorn", "asyncio", 
        "pydantic", "pydantic_settings", "python-dotenv"
    ]
    
    missing_deps = []
    
    # Verificar cada dependência
    for dep in critical_deps:
        try:
            # Tenta importar o módulo
            if dep == "python-dotenv":
                importlib.import_module("dotenv")
            elif dep == "pydantic_settings":
                importlib.import_module("pydantic_settings")
            else:
                importlib.import_module(dep)
        except ImportError:
            # Se falhar, adiciona à lista de dependências faltantes
            missing_deps.append(dep.replace("_", "-"))
    
    # Se houver dependências faltantes, instala-as
    if missing_deps:
        print(f"Dependências faltantes detectadas: {', '.join(missing_deps)}")
        print("Instalando dependências...")
        
        # Instala as dependências faltantes
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
            print("✅ Dependências instaladas com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            print("Por favor, instale manualmente as dependências faltantes:")
            print(f"  pip install {' '.join(missing_deps)}")
            return False
    else:
        print("✅ Todas as dependências críticas estão instaladas!")
    
    return True

async def wait_for_api(max_wait_time=MAX_WAIT_TIME):
    """
    Aguarda até que a API esteja online por um período de tempo.
    Retorna True se a API estiver online, False caso contrário.
    """
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:8000/")
                if response.status_code == 200:
                    print(f"✅ API online! Status: {response.status_code}")
                    print(f"Resposta: {response.text}")
                    return True
        except Exception as e:
            pass
        
        # Aguarda antes de tentar novamente
        await asyncio.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    
    print(f"\n❌ API não está respondendo após {max_wait_time} segundos")
    return False

async def test_search_api():
    """
    Testa a API de busca com uma pergunta PICOTT de exemplo
    """
    # Primeiro verificar se a API está online
    print("Verificando disponibilidade da API...")
    api_online = await wait_for_api()
    if not api_online:
        print("Teste cancelado: API não está disponível")
        return False
    
    # URL da API local
    url = "http://localhost:8000/api/search"
    
    # Exemplo de consulta PICOTT
    payload = {
        "picott_text": "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
    }
    
    print("\nEnviando requisição para a API...")
    
    # Faz a requisição para a API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Tentando fazer requisição POST para /api/search...")
            response = await client.post(url, json=payload)
            
            # Exibe o código de status
            print(f"Status: {response.status_code}")
            
            # Se a requisição for bem-sucedida, exibe a resposta
            if response.status_code == 200:
                result = response.json()
                print("\nResposta da API:")
                print(f"Consulta original: {result['original_query']}")
                print(f"Melhor consulta PubMed: {result['best_pubmed_query']}")
                print(f"\nNúmero de iterações: {len(result['iterations'])}")
                return True
            else:
                print(f"Erro na requisição: {response.text}")
                return False
    
    except httpx.ReadTimeout:
        print("Timeout ao esperar resposta da API. A operação está demorando mais do que o esperado.")
        return False
    except Exception as e:
        print(f"Erro ao fazer a requisição: {str(e)}")
        return False

async def test_api_availability():
    """
    Teste simplificado que verifica apenas se a API está disponível
    """
    print("Verificando disponibilidade da API...")
    api_online = await wait_for_api()
    
    if api_online:
        print("\n✅ Teste de disponibilidade: API está online e respondendo!")
        return True
    else:
        print("\n❌ Teste de disponibilidade: API não está respondendo!")
        return False

def main():
    # Verificar e instalar dependências
    if not check_and_install_dependencies():
        print("❌ Não foi possível continuar devido a dependências faltantes.")
        return

    # Verificar qual teste executar
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        print("Executando teste completo da API...")
        result = asyncio.run(test_search_api())
    else:
        print("Executando teste simples de disponibilidade...")
        result = asyncio.run(test_api_availability())
    
    # Encerrar com código de saída apropriado
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main() 
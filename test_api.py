import asyncio
import httpx
import json
import traceback
import time
import sys

# Configurar tempo de espera máximo para testes
MAX_WAIT_TIME = 30  # segundos

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
        print("Teste cancelado: API não está disponível. Certifique-se de iniciar o servidor FastAPI com 'uvicorn app.main:app --reload'")
        return
    
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
                
                # Exibe detalhes da primeira iteração
                if result['iterations']:
                    first_iter = result['iterations'][0]
                    print(f"\nPrimeira iteração:")
                    print(f"Query: {first_iter['query']}")
                    print(f"Número de resultados: {first_iter['result_count']}")
                    print(f"Razão para refinamento: {first_iter['refinement_reason']}")
            else:
                print(f"Erro na requisição: {response.text}")
    
    except httpx.ReadTimeout:
        print("Timeout ao esperar resposta da API. A operação está demorando mais do que o esperado.")
    except Exception as e:
        print(f"Erro ao fazer a requisição: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")

if __name__ == "__main__":
    # Executa o teste de forma assíncrona
    asyncio.run(test_search_api())

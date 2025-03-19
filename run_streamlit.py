import asyncio
import httpx
import json
import traceback

async def test_search_api():
    """
    Testa a API de busca com uma pergunta PICOTT de exemplo
    """
    # URL da API local
    url = "http://localhost:8000/api/search"
    
    # Exemplo de consulta PICOTT
    payload = {
        "picott_text": "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
    }
    
    print("Enviando requisição para a API...")
    
    # Primeiro, vamos verificar se o servidor está acessível
    try:
        async with httpx.AsyncClient() as client:
            health_response = await client.get("http://localhost:8000/")
            print(f"Servidor está acessível. Status: {health_response.status_code}")
            print(f"Resposta da raiz: {health_response.text}")
    except Exception as e:
        print(f"Erro ao verificar servidor: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
    
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

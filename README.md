# Agente de Busca Otimizada para PubMed

Este projeto implementa um agente inteligente para otimizar buscas no PubMed utilizando Modelos de Linguagem (LLMs) para gerar e refinar consultas com base em perguntas clínicas no formato PICOTT.

## Estrutura do Projeto

```
pubmed_search/
├── app/
│   ├── api/             # Endpoints da API
│   ├── core/            # Configurações centrais
│   ├── frontend/        # Interface Streamlit
│   ├── models/          # Modelos de dados
│   ├── services/        # Serviços de negócio
│   ├── tests/           # Testes automatizados
│   ├── utils/           # Utilitários
│   └── main.py          # Ponto de entrada da aplicação
├── logs/                # Diretório para arquivos de log
├── .env                 # Variáveis de ambiente
└── requirements.txt     # Dependências
```

## Funcionalidades

- Geração de consultas otimizadas para o PubMed a partir de perguntas no formato PICOTT
- Refinamento iterativo das consultas com base nos resultados obtidos
- Análise de relevância e qualidade dos resultados da pesquisa
- Interface web amigável com Streamlit para visualizar todo o processo de refinamento
- Ajuste automático da estratégia de busca com base no número de resultados encontrados

## Estratégia de Refinamento

O sistema utiliza uma estratégia sofisticada de refinamento que:

1. Prioriza os elementos de População e Intervenção nas consultas
2. Adiciona nomes comerciais de medicamentos quando identificados
3. Evita termos genéricos como "study", "research", "patients" sem qualificadores
4. Ajusta a amplitude da consulta conforme o número de resultados
5. Remove termos de comparação e tempo quando há poucos resultados
6. Adiciona especificações quando há muitos resultados

## Interface Streamlit

O projeto inclui uma interface web interativa construída com Streamlit que permite:
- Formular perguntas no formato PICOTT
- Visualizar todo o processo de geração e refinamento da consulta
- Ver as diferenças entre cada versão da consulta
- Configurar o número de iterações e parâmetros de refinamento
- Visualizar os resultados finais com links diretos para o PubMed

## Como Executar

1. Instale as dependências:
```
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente (crie um arquivo .env):
```
OPENAI_API_KEY=sua_chave_aqui
DEEPSEEK_API_KEY=sua_chave_aqui
```

3. Execute a interface Streamlit:
```
streamlit run app/frontend/streamlit_app.py
```

4. Ou execute a API FastAPI:
```
uvicorn app.main:app --reload
```

## Requisitos

- Python 3.10+
- Streamlit
- FastAPI
- Bibliotecas Python listadas em requirements.txt
- Chaves de API para os serviços LLM (OpenAI, DeepSeek)

## Contribuições

Contribuições são bem-vindas! Por favor, siga estas etapas:
1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/nova-funcionalidade`)
3. Implemente suas mudanças
4. Execute os testes
5. Faça commit das alterações (`git commit -m 'Adiciona nova funcionalidade'`)
6. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
7. Abra um Pull Request

## Instalação

1. Clone o repositório:

```bash
git clone https://seu-repositorio/pubmed_search.git
cd pubmed_search
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
# No Windows
venv\Scripts\activate
# No Linux/Mac
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente no arquivo `.env` (já criado com suas chaves de API)

## Execução

Para iniciar o servidor:

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`, e a documentação interativa (Swagger UI) em `http://localhost:8000/docs`.

## Uso da API

### Endpoint Principal

`POST /api/search`

Corpo da requisição:
```json
{
  "picott_text": "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
}
```

Resposta:
```json
{
  "original_query": "Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)",
  "best_pubmed_query": "(\"diabetes tipo 2\"[tiab] OR \"DM2\"[tiab]) AND (\"metformina\"[tiab] OR \"biguanida\"[tiab]) AND \"HbA1c\"[tiab] AND (\"randomized controlled trial\"[tiab] OR \"RCT\"[tiab]) AND \"6 months\"[tiab]",
  "iterations": [
    {
      "iteration_number": 1,
      "query": "\"diabetes tipo 2\"[tiab] AND \"metformina\"[tiab] AND \"HbA1c\"[tiab] AND \"randomized controlled trial\"[tiab] AND \"6 months\"[tiab]",
      "result_count": 12,
      "evaluation": {
        "total_count": 12,
        "count_score": 0.12,
        "primary_studies_ratio": 0.8,
        "systematic_reviews_ratio": 0.0,
        "average_relevance": 0.56,
        "overall_score": 0.34,
        "issues": "Consulta muito específica, poucos resultados encontrados"
      },
      "refinement_reason": "Consulta inicial gerada a partir do texto PICOTT"
    },
    {
      "iteration_number": 2,
      "query": "(\"diabetes tipo 2\"[tiab] OR \"DM2\"[tiab]) AND (\"metformina\"[tiab] OR \"biguanida\"[tiab]) AND \"HbA1c\"[tiab] AND (\"randomized controlled trial\"[tiab] OR \"RCT\"[tiab]) AND \"6 months\"[tiab]",
      "result_count": 38,
      "evaluation": {
        "total_count": 38,
        "count_score": 0.38,
        "primary_studies_ratio": 0.8,
        "systematic_reviews_ratio": 0.2,
        "average_relevance": 0.62,
        "overall_score": 0.55,
        "issues": "Consulta relativamente específica, considere ampliar os termos"
      },
      "refinement_reason": "Refinamento necessário para corrigir: Consulta muito específica, poucos resultados encontrados"
    }
  ]
}
```

## Componentes Principais

1. **QueryGenerator**: Transforma a pergunta PICOTT em consulta PubMed estruturada
2. **PubMedService**: Comunica-se com a API do PubMed para buscar artigos
3. **QueryEvaluator**: Avalia e refina iterativamente a consulta para obter resultados ótimos

## Configurações

Todas as configurações são carregadas do arquivo `.env` e podem ser acessadas através do módulo `app.core.config`.

## API do PubMed

O agente utiliza a API NCBI E-utilities para realizar as consultas no PubMed. Isso permite a busca eficiente e o acesso a metadados detalhados dos artigos.

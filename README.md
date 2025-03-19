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

## Melhorias na Interface do Usuário
- Adicionadas opções avançadas de pesquisa
- Implementada a visualização detalhada de filtros aplicados
- Adicionada explicação sobre a eficácia e fonte de cada filtro
- Implementado sistema de exportação de consulta em múltiplos formatos

## Configuração do Ambiente

### Configuração Local
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Copie o arquivo `.env.example` para `.env` e preencha com suas chaves de API
4. Execute a aplicação: `python run_streamlit.py`

### Configuração no Streamlit Cloud
Para implantar a aplicação no Streamlit Cloud, siga estas etapas:

1. Faça o upload do código para um repositório GitHub
2. Conecte o Streamlit Cloud ao seu repositório
3. Configure as secrets necessárias no dashboard do Streamlit Cloud:
   - Acesse "App settings" > "Secrets" 
   - Adicione as seguintes variáveis no formato TOML:
   ```toml
   OPENAI_API_KEY = "sua-chave-aqui"
   DEEPSEEK_API_KEY = "sua-chave-aqui"
   ANTHROPIC_API_KEY = "sua-chave-aqui" # opcional
   OPENROUTER_API_KEY = "sua-chave-aqui" # opcional
   GEMINI_API_KEY = "sua-chave-aqui" # opcional
   PUBMED_EMAIL = "seu-email@example.com"
   ```
4. Defina como arquivo principal: `run_streamlit.py`
5. Inicie o deploy

Observação: A aplicação verificará automaticamente se as chaves de API obrigatórias estão configuradas e exibirá uma mensagem de erro caso estejam faltando.

## Arquitetura do Sistema

O sistema utiliza uma arquitetura distribuída:

1. **Backend/API**: Hospedado em um servidor VPS dedicado
   - FastAPI para criar endpoints RESTful
   - Gunicorn como servidor de produção
   - Implementação de busca otimizada para PubMed

2. **Frontend**: Hospedado no Streamlit Cloud
   - Interface de usuário intuitiva
   - Conecta-se à API hospedada na VPS
   - Processamento de formulários e exibição de resultados

Esta arquitetura resolve o problema de limitações do Streamlit Cloud, permitindo que a API possa ser executada com todas as dependências necessárias no servidor VPS, enquanto o frontend permanece no ambiente especializado do Streamlit Cloud.

## Execução

### Método 1: Inicialização Unificada (Recomendado para Desenvolvimento)

Para iniciar tanto a API quanto a interface Streamlit com um único comando:

```bash
python start_pubmed_agent.py
```

Este script iniciará automaticamente a API FastAPI na porta 8000 e a interface Streamlit na porta 8501.

### Método 2: Inicialização Separada

Para iniciar o servidor:

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`, e a documentação interativa (Swagger UI) em `http://localhost:8000/docs`.

Para iniciar a interface Streamlit em outra janela de terminal:

```bash
python run_streamlit.py
```

Ou diretamente com o Streamlit:

```bash
streamlit run app/frontend/streamlit_app.py
```

### Verificando a Instalação

Para verificar se a API está funcionando corretamente:

```bash
python test_api_only.py  # Teste simples de disponibilidade
python test_api_only.py --full  # Teste completo com uma consulta
```

Para verificar o deploy no Streamlit Cloud:

```bash
python test_deploy.py
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

## Uso da API

### Endpoint Principal

`
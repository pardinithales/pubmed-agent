# Deploy da API PubMed no Vercel

Este guia explica como implantar a API do PubMed Agent no Vercel enquanto mantém o frontend Streamlit no Streamlit Cloud.

## Arquitetura

A solução usa uma arquitetura distribuída:

1. **Backend/API**: Hospedado no Vercel como função serverless
2. **Frontend**: Hospedado no Streamlit Cloud

Esta abordagem resolve o problema de rodar a API no ambiente Streamlit Cloud, que não permite a execução de serviços em segundo plano.

## Pré-requisitos

- Conta no [Vercel](https://vercel.com)
- Conta no [Streamlit Cloud](https://streamlit.io/cloud)
- Git instalado localmente

## Configuração do Deploy no Vercel

### Passo 1: Preparar o projeto para o Vercel

Os arquivos necessários já estão configurados:
- `vercel.json`: Configurações do Vercel
- `api_server.py`: Ponto de entrada para o Vercel
- `requirements-vercel.txt`: Dependências específicas para o Vercel

### Passo 2: Deploy no Vercel

1. Faça login no Vercel e conecte-o ao seu repositório GitHub
2. Importe o projeto
3. Configure as variáveis de ambiente:
   - `OPENAI_API_KEY`: Sua chave de API da OpenAI
   - `DEEPSEEK_API_KEY`: Sua chave de API da DeepSeek (se necessário)
4. Em "Build and Output Settings":
   - Build Command: `pip install -r requirements-vercel.txt`
   - Output Directory: deixe em branco
5. Clique em "Deploy"

### Passo 3: Configurar o Streamlit Cloud

1. Faça login no Streamlit Cloud
2. Crie um novo app apontando para o arquivo `streamlit_app.py`
3. Configure os secrets no Streamlit:
   ```
   [general]
   API_URL = "https://seu-app-vercel.vercel.app"
   OPENAI_API_KEY = "sua-chave-aqui"
   DEEPSEEK_API_KEY = "sua-chave-aqui"
   ```
4. Salve as configurações e implante o aplicativo

## Testando a Integração

Após ambos os deploys (Vercel e Streamlit Cloud) estarem concluídos:

1. Acesse a URL da sua API no Vercel diretamente para verificar se está online
2. Acesse o aplicativo Streamlit e verifique se ele consegue se conectar à API
3. Teste o formulário de consulta para verificar se está funcionando corretamente

## Execução Local

Para executar o sistema localmente, você pode:

1. Usar a API local:
```
python run_local.py --api local
```

2. Usar a API remota no Vercel:
```
python run_local.py --api remote --url https://seu-app-vercel.vercel.app
```

## Solução de Problemas

### API no Vercel retorna erro

- Verifique os logs no dashboard do Vercel
- Confirme se todas as variáveis de ambiente estão configuradas
- Teste localmente com `uvicorn api_server:app --reload`

### Streamlit não conecta à API

- Verifique se o URL da API está correto nos secrets do Streamlit
- Confirme se o CORS está configurado corretamente no Vercel
- Teste a URL da API diretamente no navegador para ver se está acessível

### Dicas para Depuração

1. Use o endpoint raiz da API (`/`) para verificar se está online
2. Verifique os logs do Vercel para erros de inicialização
3. Teste a API localmente antes do deploy no Vercel 
import streamlit as st
import sys
import os
import importlib.util
import traceback
from pathlib import Path

st.set_page_config(
    page_title="Debug Deploy - PubMed Agent",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Diagnóstico de Deploy - PubMed Agent")

# Verificar diretório atual e paths
st.header("1. Verificação de Ambiente")
cwd = os.getcwd()
st.write(f"Diretório atual: {cwd}")
st.write(f"Python path: {sys.path}")

# Verificar estrutura de arquivos
st.header("2. Estrutura de Arquivos")
root_files = [str(p) for p in Path(cwd).glob("*") if not p.name.startswith(".")]
st.write("Arquivos na raiz:", root_files)

app_path = Path(cwd) / "app"
if app_path.exists():
    app_files = [str(p) for p in app_path.glob("**/*") if p.is_file()]
    st.write("Arquivos na pasta app:", app_files)
else:
    st.error("❌ Pasta 'app' não encontrada!")

# Verificar dependências
st.header("3. Verificação de Dependências")
required_packages = [
    "streamlit", "asyncio", "httpx", "openai", 
    "pydantic", "fastapi", "loguru"
]

for package in required_packages:
    try:
        spec = importlib.util.find_spec(package)
        if spec is not None:
            module = importlib.import_module(package)
            st.write(f"✅ {package}: {getattr(module, '__version__', 'Versão desconhecida')}")
        else:
            st.error(f"❌ {package}: Não encontrado!")
    except Exception as e:
        st.error(f"❌ {package}: Erro ao importar - {str(e)}")

# Verificar secrets e variáveis de ambiente
st.header("4. Verificação de Secrets e Variáveis de Ambiente")
api_keys = [
    "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY", "GEMINI_API_KEY"
]

env_status = {}
for key in api_keys:
    env_value = os.environ.get(key)
    env_status[key] = "✅ Presente" if env_value else "❌ Ausente"

st.write("Variáveis de ambiente:", env_status)

has_secrets = hasattr(st, "secrets")
st.write(f"Tem acesso a secrets: {'✅ Sim' if has_secrets else '❌ Não'}")

if has_secrets:
    secret_keys = []
    for key in api_keys:
        if key in st.secrets:
            secret_keys.append(f"✅ {key}")
        else:
            secret_keys.append(f"❌ {key}")
    st.write("Secrets disponíveis:", secret_keys)

# Teste de importação de módulos específicos
st.header("5. Teste de Importação de Módulos")

try:
    sys.path.append(str(Path(cwd)))
    frontend_path = Path(cwd) / "app" / "frontend" / "streamlit_app.py"
    
    if frontend_path.exists():
        st.write(f"✅ Arquivo streamlit_app.py encontrado em: {frontend_path}")
        
        try:
            # Tentar importar serviços específicos
            from app.services.query_generator import QueryGenerator
            st.write("✅ Importação de QueryGenerator bem-sucedida")
        except Exception as e:
            st.error(f"❌ Erro ao importar QueryGenerator: {str(e)}")
            st.code(traceback.format_exc(), language="python")
            
        try:
            from app.services.pubmed_service import PubMedService
            st.write("✅ Importação de PubMedService bem-sucedida")
        except Exception as e:
            st.error(f"❌ Erro ao importar PubMedService: {str(e)}")
            st.code(traceback.format_exc(), language="python")
    else:
        st.error(f"❌ Arquivo streamlit_app.py não encontrado em: {frontend_path}")
except Exception as e:
    st.error(f"❌ Erro durante o teste de importação: {str(e)}")
    st.code(traceback.format_exc(), language="python")

# Botão para iniciar a aplicação manualmente
st.header("6. Iniciar Aplicação Manualmente")

if st.button("Tentar iniciar a aplicação principal"):
    try:
        st.info("Tentando iniciar a aplicação principal...")
        # Criar iframe para evitar que erros na aplicação principal afetem esta página
        st.components.v1.iframe(f"{st.secrets.get('STREAMLIT_SERVER_URL', '')}/app/frontend/streamlit_app", height=600)
    except Exception as e:
        st.error(f"❌ Erro ao iniciar a aplicação: {str(e)}")
        st.code(traceback.format_exc(), language="python") 
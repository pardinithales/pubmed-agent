import streamlit as st
import os

st.title("Teste de Deploy")

# Verificar se estamos no ambiente Streamlit Cloud
is_cloud = os.environ.get('STREAMLIT_SHARING') == 'true' or os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app')
st.write(f"Executando no Streamlit Cloud: {is_cloud}")

# Mostrar variáveis de ambiente (sem exibir valores sensíveis)
env_vars = {}
for key in os.environ:
    if 'API_KEY' in key:
        env_vars[key] = "***** (valor oculto)"
    else:
        env_vars[key] = os.environ[key]

st.subheader("Variáveis de ambiente")
st.json(env_vars)

# Verificar secrets do Streamlit
st.subheader("Secrets do Streamlit")
has_secrets = hasattr(st, "secrets")
st.write(f"Tem acesso a secrets: {has_secrets}")

if has_secrets:
    secret_keys = list(st.secrets.keys()) if hasattr(st.secrets, "keys") else []
    st.write(f"Chaves disponíveis: {secret_keys}")

# Informações de versão
st.subheader("Informações de versão")
import sys
st.write(f"Python: {sys.version}")
st.write(f"Streamlit: {st.__version__}")

st.success("Se você está vendo esta mensagem, o teste de deploy foi bem-sucedido!") 
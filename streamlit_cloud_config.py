"""
Arquivo de configuração específico para o Streamlit Cloud.
Este arquivo é automaticamente executado pelo Streamlit Cloud no início da aplicação.
"""
import streamlit as st
import os
import sys

# Configurar variáveis de ambiente para otimização
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"  
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5"  # Limitar tamanho de upload
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"  # Desativar estatísticas
os.environ["STREAMLIT_THEME_BASE"] = "light"  # Tema mais leve
os.environ["FORCE_SIMPLE_APP"] = "true"  # Flag para forçar app simples
os.environ["API_OFFLINE_MODE"] = "true"  # Flag para indicar que API não está disponível

# Configurar formato dos logs do Streamlit
os.environ["STREAMLIT_LOG_LEVEL"] = "info"

# Imprimir informações de diagnóstico nos logs
print(f"Streamlit Cloud Config inicializado")
print(f"Python: {sys.version}")
print(f"Streamlit: {st.__version__}")
try:
    import pydantic
    print(f"Pydantic: {pydantic.__version__}")
    import pydantic_settings
    print(f"Pydantic-settings: OK")
except ImportError as e:
    print(f"Erro ao importar módulos: {e}") 
import streamlit as st
import sys
import os
from pathlib import Path

# Configurações mínimas da página
st.set_page_config(
    page_title="PubMed Agent (Versão Simplificada)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"  # Iniciar com sidebar recolhida para acelerar carregamento
)

# Configurar o caminho para o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

# Título e descrição
st.title("🔍 Assistente de Consultas PubMed (Versão Simplificada)")
st.markdown("Esta é uma versão simplificada do aplicativo para diagnóstico. Utilize-a quando a versão completa estiver com problemas.")

# Verificar status de inicialização
st.success("✅ Aplicativo inicializado com sucesso!")

# Mostrar informações básicas sobre o ambiente
st.subheader("Informações do Ambiente")
env_info = {
    "Ambiente": "Streamlit Cloud" if os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app') else "Local",
    "Modo Simplificado": "Ativo",
    "Diretório Raiz": str(root_dir)
}
st.json(env_info)

# Status das chaves de API - versão simplificada
st.subheader("Status das Chaves de API")
api_keys = {
    "OPENAI_API_KEY": "✅ Configurada" if os.environ.get("OPENAI_API_KEY") or (hasattr(st, "secrets") and st.secrets.get("OPENAI_API_KEY")) else "❌ Não configurada",
    "DEEPSEEK_API_KEY": "✅ Configurada" if os.environ.get("DEEPSEEK_API_KEY") or (hasattr(st, "secrets") and st.secrets.get("DEEPSEEK_API_KEY")) else "❌ Não configurada",
}
st.json(api_keys)

# Formulário simplificado
st.subheader("Consulta PubMed Simplificada")

with st.form("picott_form_simple"):
    picott_text = st.text_area(
        "Digite sua pergunta clínica:",
        height=100,
        placeholder="Ex: Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O)"
    )
    
    submit_button = st.form_submit_button("Gerar Consulta")

# Processar quando o formulário for enviado
if submit_button and picott_text:
    st.subheader("Consulta Gerada")
    
    # Simulação de consulta para demonstração
    st.code(f"""
    ((População OR seu sinônimo OR outro termo) 
    AND 
    (Intervenção OR seu sinônimo OR outro termo))
    
    Sua consulta original:
    {picott_text}
    """)
    
    st.info("Este é apenas um exemplo de consulta. Na versão completa do aplicativo, a consulta seria gerada por um modelo de IA.")

# Explicação sobre a versão simplificada
st.markdown("---")
st.markdown("""
### Por que estou vendo a versão simplificada?

Esta versão simplificada foi criada para ajudar a diagnosticar problemas no deploy da versão completa do aplicativo.

A equipe de desenvolvimento está trabalhando para resolver os problemas na versão completa. Por favor, aguarde ou entre em contato com o suporte.
""")

# Link para diagnóstico - removido para simplificar ainda mais 

import streamlit as st
import sys
import os
from pathlib import Path

# Configurações da página
st.set_page_config(
    page_title="PubMed Agent (Versão Simplificada)",
    page_icon="🔍",
    layout="wide"
)

# Configurar o caminho para o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

st.title("🔍 Assistente de Consultas PubMed (Versão Simplificada)")
st.markdown("Esta é uma versão simplificada do aplicativo para debug. Utilize-a quando a versão completa estiver com problemas.")

# Mostrar status das chaves de API
st.header("Status das Chaves de API")

api_keys = {
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY") or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None),
    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY") or (st.secrets.get("DEEPSEEK_API_KEY") if hasattr(st, "secrets") else None),
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY") or (st.secrets.get("ANTHROPIC_API_KEY") if hasattr(st, "secrets") else None),
    "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY") or (st.secrets.get("OPENROUTER_API_KEY") if hasattr(st, "secrets") else None),
    "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY") or (st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None)
}

for key, value in api_keys.items():
    if value:
        st.success(f"{key}: ✅ Configurada")
    else:
        st.error(f"{key}: ❌ Não configurada")

# Formulário simplificado
st.header("Consulta PubMed Simplificada")

with st.form("picott_form_simple"):
    picott_text = st.text_area(
        "Digite sua pergunta clínica no formato PICOTT:",
        height=150,
        placeholder="P: População\nI: Intervenção\nC: Comparação\nO: Desfecho (Outcome)\nT: Tipo de estudo\nT: Tempo"
    )
    
    submit_button = st.form_submit_button("Gerar Consulta")

# Processar quando o formulário for enviado
if submit_button and picott_text:
    st.header("Consulta Gerada")
    
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
    st.header("Por que estou vendo a versão simplificada?")
    st.markdown("""
    Esta versão simplificada foi criada para ajudar a diagnosticar problemas no deploy da versão completa do aplicativo.
    
    Possíveis razões para problemas no deploy:
    1. **Configuração de chaves de API:** Verifique se todas as chaves necessárias estão configuradas no Streamlit Cloud.
    2. **Problemas de importação:** Pode haver erros ao importar módulos específicos.
    3. **Timeout de requisições:** A geração da consulta pode estar excedendo o tempo limite.
    
    Para resolver:
    1. Acesse o painel de controle do Streamlit Cloud e verifique as secrets.
    2. Verifique os logs para identificar erros específicos.
    3. Se necessário, ajuste o código para torná-lo mais simples e robusto.
    """)

# Link para a página de debug
st.markdown("---")
st.markdown("[Acessar Diagnóstico de Deploy](debug_deploy) | [Acessar Teste Básico](test_deploy)") 
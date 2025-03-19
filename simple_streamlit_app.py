import streamlit as st
import sys
import os
import json
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

# Detectar ambiente
is_cloud = os.environ.get('STREAMLIT_SHARING') == 'true' or os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app')
mode = "Cloud" if is_cloud else "Local"

# Título e descrição
st.title("🔍 Assistente de Consultas PubMed (Versão Simplificada)")
st.markdown("Esta é uma versão simplificada do aplicativo para diagnóstico. Utilize-a quando a versão completa estiver com problemas.")

# Verificar status de inicialização
st.success(f"✅ Aplicativo inicializado com sucesso no ambiente {mode}!")

# Mostrar informações básicas sobre o ambiente
st.subheader("Informações do Ambiente")
env_info = {
    "Ambiente": mode,
    "Modo Simplificado": "Ativo",
    "Diretório Raiz": str(root_dir),
    "Versão Python": sys.version,
    "Versão Streamlit": st.__version__
}
st.json(env_info)

# Status das chaves de API - versão simplificada
st.subheader("Status das Chaves de API")
api_keys = {
    "OPENAI_API_KEY": "✅ Configurada" if os.environ.get("OPENAI_API_KEY") or (hasattr(st, "secrets") and st.secrets.get("OPENAI_API_KEY")) else "❌ Não configurada",
    "DEEPSEEK_API_KEY": "✅ Configurada" if os.environ.get("DEEPSEEK_API_KEY") or (hasattr(st, "secrets") and st.secrets.get("DEEPSEEK_API_KEY")) else "❌ Não configurada",
}
st.json(api_keys)

# Adicionar switch para modo offline
st.sidebar.header("Configurações")
offline_mode = st.sidebar.checkbox("Modo Offline (Simulado)", value=True, help="Ative para usar o modo offline sem API")

# Explicar o modo offline
if offline_mode:
    st.info("🔌 **Modo Offline Ativado**: As consultas serão simuladas sem acessar a API.")

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
    
    with st.spinner("Gerando consulta otimizada..."):
        # Simular um breve processamento
        import time
        time.sleep(1.5)
        
        # Gerar consulta simulada para demonstração
        termos_p = [palavra for palavra in picott_text.split() if len(palavra) > 3][:3]
        termos_i = [palavra for palavra in picott_text.split() if len(palavra) > 4][3:5]
        
        # Consulta simulada
        consulta_simulada = f"""
        (("{termos_p[0]}"[tiab] OR "{termos_p[1]}"[tiab]) 
        AND 
        ("{termos_i[0]}"[tiab] OR "{termos_i[1]}"[tiab]))
        """
        
        # Mostrar a consulta gerada
        st.code(consulta_simulada, language="text")
        
        # Simular resposta completa da API
        resposta_simulada = {
            "original_query": picott_text,
            "best_pubmed_query": consulta_simulada.strip(),
            "iterations": [
                {
                    "iteration_number": 1,
                    "query": consulta_simulada.strip(),
                    "result_count": 42,
                    "refinement_reason": "Consulta inicial gerada a partir do texto PICOTT"
                }
            ]
        }
        
        # Exibir dados simulados em um formato amigável
        st.subheader("Detalhes da Consulta")
        st.markdown(f"**Número de resultados estimados:** 42 artigos")
        st.markdown(f"**Eficácia da consulta:** ⭐⭐⭐⭐ (Simulada)")
        
        # Oferecer opção para ver resposta JSON completa
        if st.checkbox("Ver resposta JSON completa (simulada)"):
            st.json(resposta_simulada)
        
        # Adicionar link para PubMed
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={consulta_simulada.strip().replace(' ', '+')}"
        st.markdown(f"[Abrir esta consulta no PubMed ↗](https://pubmed.ncbi.nlm.nih.gov)")

# Explicação sobre a versão simplificada
st.markdown("---")
st.markdown("""
### Por que estou vendo a versão simplificada?

Esta versão simplificada foi criada para:
1. **Diagnosticar problemas** no deploy da versão completa do aplicativo
2. **Funcionar de forma independente** sem necessidade da API backend
3. **Demonstrar a funcionalidade básica** do sistema completo

Na versão completa, as consultas são geradas por modelos de IA através da API FastAPI, mas aqui usamos uma simulação para mostrar como funcionaria.
""")

# Footer com informações adicionais
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8em;">
Versão Simplificada 1.1 | Modo Offline | PubMed Agent
</div>
""", unsafe_allow_html=True) 
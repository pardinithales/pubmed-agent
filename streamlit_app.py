import streamlit as st
import sys
import os
import json
import httpx
import asyncio
from pathlib import Path

# Configurações mínimas da página
st.set_page_config(
    page_title="PubMed Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"  # Iniciar com sidebar recolhida para acelerar carregamento
)

# Configurar o caminho para o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

# Detectar ambiente
is_cloud = os.environ.get('STREAMLIT_SHARING') == 'true' or os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app')
mode = "Cloud" if is_cloud else "Local"

# URL da API - usar a URL da VPS em produção
API_BASE_URL = "http://5.161.199.194:8080"  # API hospedada na VPS
LOCAL_API_URL = "http://localhost:8000"

# Definir URL da API baseado no ambiente (sempre usar a VPS no Streamlit Cloud)
api_url = API_BASE_URL if is_cloud else LOCAL_API_URL

# Título e descrição
st.title("🔍 Assistente de Consultas PubMed")
st.markdown("Transforme sua pergunta clínica em consultas otimizadas para o PubMed usando Inteligência Artificial.")

# Verificar status de inicialização
st.success(f"✅ Aplicativo inicializado com sucesso no ambiente {mode}!")

# Mostrar informações sobre a API na sidebar
with st.sidebar:
    st.header("Informações da API")
    api_status = st.empty()
    
    # Verificar status da API
    try:
        response = httpx.get(f"{api_url}/", timeout=5.0)
        if response.status_code == 200:
            api_info = response.json()
            api_status.success(f"✅ API conectada: {api_info.get('service', 'Serviço PubMed')} ({api_info.get('environment', 'prod')})")
            st.json(api_info)
        else:
            api_status.error(f"❌ API retornou status {response.status_code}")
    except Exception as e:
        api_status.error(f"❌ Não foi possível conectar à API: {str(e)}")
        st.info("Alguns recursos podem estar indisponíveis sem conexão com a API.")

# Mostrar informações básicas sobre o ambiente
st.subheader("Informações do Ambiente")
env_info = {
    "Ambiente": mode,
    "API URL": api_url,
    "Versão Python": sys.version,
    "Versão Streamlit": st.__version__
}
st.json(env_info)

# Status das chaves de API
st.subheader("Status das Chaves de API")
api_keys = {
    "OPENAI_API_KEY": "✅ Configurada" if os.environ.get("OPENAI_API_KEY") or (hasattr(st, "secrets") and st.secrets.get("OPENAI_API_KEY")) else "❌ Não configurada",
    "DEEPSEEK_API_KEY": "✅ Configurada" if os.environ.get("DEEPSEEK_API_KEY") or (hasattr(st, "secrets") and st.secrets.get("DEEPSEEK_API_KEY")) else "❌ Não configurada",
}
st.json(api_keys)

# Explicar como funciona a aplicação
with st.expander("Como funciona?"):
    st.markdown("""
    ### Processo de Otimização de Consultas
    
    1. **Digite sua pergunta clínica** no formato PICOTT (População, Intervenção, Comparação, Resultado, Tipo de estudo, Tempo).
    2. **A IA analisa sua pergunta** e identifica os elementos-chave.
    3. **Geração de consulta otimizada** usando os melhores termos e operadores para o PubMed.
    4. **Avaliação de resultados** para garantir que a consulta retorne estudos relevantes.
    5. **Refinamento iterativo** até obter a melhor consulta possível.
    """)

# Formulário para entrada do usuário
st.subheader("Formulário de Consulta")

# Separar a entrada de dados do formulário para debugging
picott_text = st.text_area(
    "Digite sua pergunta clínica no formato PICOTT:",
    height=100,
    placeholder="Ex: Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
)

col1, col2 = st.columns([1, 1])
with col1:
    max_iterations = st.slider("Número máximo de iterações", 1, 5, 3)
with col2:
    use_offline = st.checkbox("Usar modo offline (se API indisponível)", value=False)

# Botão simples fora do formulário
submit_button = st.button("Gerar Consulta Otimizada", type="primary", use_container_width=True)

# Função para consultar a API
async def query_api(text, max_iterations=3):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_url}/api/search",
                json={"picott_text": text, "max_iterations": max_iterations}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Erro da API: {response.text}")
                return None
    except Exception as e:
        st.error(f"Erro ao consultar API: {str(e)}")
        return None

# Função para simulação de consulta offline
def simulate_query(text):
    """Simula uma resposta da API quando offline."""
    # Gerar termos a partir do texto
    termos_p = [palavra for palavra in text.split() if len(palavra) > 3][:3]
    termos_i = [palavra for palavra in text.split() if len(palavra) > 4][3:5]
    
    # Gerar consulta simulada
    consulta_simulada = f"""
    (("{termos_p[0]}"[tiab] OR "{termos_p[1]}"[tiab]) 
    AND 
    ("{termos_i[0]}"[tiab] OR "{termos_i[1]}"[tiab]))
    """.strip()
    
    # Resposta simulada
    return {
        "original_query": text,
        "best_pubmed_query": consulta_simulada,
        "iterations": [
            {
                "iteration_number": 1,
                "query": consulta_simulada,
                "result_count": 42,
                "refinement_reason": "Consulta inicial (simulação)"
            }
        ],
        "simulation": True
    }

# Processar quando o botão for clicado
if submit_button and picott_text:
    with st.spinner("Gerando consulta otimizada para PubMed..."):
        result = None
        
        if not use_offline:
            # Tentar usar a API
            try:
                result = asyncio.run(query_api(picott_text, max_iterations))
            except Exception as e:
                st.warning(f"Não foi possível usar a API: {str(e)}")
                st.info("Alternando para modo offline (simulado).")
        
        # Se API falhou ou modo offline solicitado, usar simulação
        if result is None:
            st.warning("Usando modo offline (simulado). A consulta gerada é simplificada.")
            result = simulate_query(picott_text)
        
        # Exibir resultados
        st.subheader("Consulta Otimizada")
        
        # Verificar se a resposta contém os campos esperados
        if result and "best_pubmed_query" in result:
            # Mostrar a consulta final otimizada
            st.code(result["best_pubmed_query"], language="text")
            
            # Detalhes da consulta
            st.subheader("Detalhes da Consulta")
            
            # Mostrar número de iterações
            num_iterations = len(result.get("iterations", []))
            st.markdown(f"**Número de iterações:** {num_iterations}")
            
            # Mostrar resultados estimados
            if num_iterations > 0:
                last_iteration = result["iterations"][-1]
                result_count = last_iteration.get("result_count", 0)
                st.markdown(f"**Número de resultados estimados:** {result_count} artigos")
            
            # Mostrar detalhes das iterações
            if st.checkbox("Ver detalhes das iterações"):
                for i, iteration in enumerate(result.get("iterations", [])):
                    with st.expander(f"Iteração {i+1}"):
                        st.code(iteration.get("query", ""), language="text")
                        st.markdown(f"**Resultados:** {iteration.get('result_count', 'N/A')}")
                        st.markdown(f"**Razão:** {iteration.get('refinement_reason', 'N/A')}")
            
            # Adicionar link para PubMed
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={result['best_pubmed_query'].replace(' ', '+')}"
            st.markdown(f"[Abrir esta consulta no PubMed ↗](https://pubmed.ncbi.nlm.nih.gov/?term={result['best_pubmed_query'].replace(' ', '+')})")
            
            # Mostrar resposta JSON completa se solicitado
            if st.checkbox("Ver resposta JSON completa"):
                st.json(result)
            
            # Adicionar aviso se estiver no modo simulado
            if result.get("simulation", False):
                st.info("⚠️ Resultados gerados em modo simulado. Para resultados mais precisos, use a API online.")
        else:
            st.error("Formato de resposta inesperado da API. Verifique os logs para mais detalhes.")
            st.json(result)

# Footer com informações
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8em;">
PubMed Agent | Versão 1.0 | API: {}
</div>
""".format(api_url), unsafe_allow_html=True) 
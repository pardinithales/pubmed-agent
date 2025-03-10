import streamlit as st
import asyncio
import sys
import os
from pathlib import Path
import urllib.parse

# Adiciona o diretório raiz ao path para poder importar os módulos da aplicação
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from app.services.query_generator import QueryGenerator
from app.services.pubmed_service import PubMedService
from app.services.query_evaluator import QueryEvaluator
from app.models.schemas import PubMedSearchResult, PICOTTQuery

# Configurações da página
st.set_page_config(
    page_title="Pesquisa PubMed - Assistente de Consultas",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para executar código assíncrono no Streamlit
async def run_async(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await func(*args, **kwargs)

# Função para destacar diferenças entre duas consultas
def highlight_query_differences(old_query, new_query):
    """
    Destaca as diferenças entre duas consultas para melhor visualização
    
    Args:
        old_query: Consulta anterior
        new_query: Consulta refinada
        
    Returns:
        str: HTML com as diferenças destacadas
    """
    import difflib
    
    d = difflib.Differ()
    diff = list(d.compare(old_query.split(), new_query.split()))
    
    # Contar quantas palavras foram adicionadas ou removidas
    added = sum(1 for word in diff if word.startswith('+ '))
    removed = sum(1 for word in diff if word.startswith('- '))
    
    # Criar HTML para exibir as diferenças
    html = "<div style='font-family: monospace; white-space: pre-wrap;'>"
    html += f"<div style='margin-bottom: 10px;'><b>Mudanças:</b> {added} adições, {removed} remoções</div>"
    
    for word in diff:
        if word.startswith('+ '):
            html += f"<span style='background-color: #CCFFCC; color: #006600;'>{word[2:]}</span> "
        elif word.startswith('- '):
            html += f"<span style='background-color: #FFCCCC; color: #CC0000;'>{word[2:]}</span> "
        elif word.startswith('  '):
            html += f"{word[2:]} "
    
    html += "</div>"
    return html

# Inicializa as classes de serviço
@st.cache_resource
def get_services():
    pubmed_service = PubMedService()
    query_generator = QueryGenerator()
    query_evaluator = QueryEvaluator(pubmed_service=pubmed_service)
    
    return {
        "query_generator": query_generator,
        "pubmed_service": pubmed_service,
        "query_evaluator": query_evaluator
    }

# Estilo personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 0;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .results-header {
        font-size: 1.3rem;
        color: #2E7D32;
        margin-top: 20px;
    }
    .step-container {
        padding: 10px;
        border-left: 3px solid #1E88E5;
        background-color: #E3F2FD;
        margin: 10px 0;
    }
    .query-initial {
        padding: 10px;
        background-color: #F1F8E9;
        border-left: 3px solid #7CB342;
        font-family: monospace;
    }
    .query-refined {
        padding: 10px;
        background-color: #FFF3E0;
        border-left: 3px solid #FB8C00;
        font-family: monospace;
    }
    .query-final {
        padding: 10px;
        background-color: #E8F5E9;
        border-left: 3px solid #43A047;
        font-family: monospace;
        font-weight: bold;
    }
    .evaluation-results {
        background-color: #E8EAF6;
        padding: 15px;
        border-radius: 5px;
        margin: 15px 0;
    }
    .article-preview {
        padding: 10px;
        background-color: #FAFAFA;
        border: 1px solid #EEEEEE;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Título e descrição
st.markdown("<h1 class='main-header'>Assistente de Pesquisa PubMed</h1>", unsafe_allow_html=True)
st.markdown("""
    <p style='text-align: center; font-size: 1.2rem;'>
        Este assistente ajuda a criar consultas otimizadas para o PubMed baseadas em questões PICOTT.
    </p>
""", unsafe_allow_html=True)

# Sidebar com informações
with st.sidebar:
    st.title("Sobre o Assistente")
    st.info("""
    **Como funciona?**
    
    1. Insira sua questão no formato PICOTT
    2. O assistente irá gerar uma consulta inicial para o PubMed
    3. A consulta será avaliada com base nos resultados obtidos
    4. Se necessário, a consulta será refinada iterativamente
    5. A consulta final otimizada será exibida
    """)
    
    st.subheader("Formato PICOTT")
    st.markdown("""
    - **P**: População/Problema
    - **I**: Intervenção
    - **C**: Comparação
    - **O**: Outcome/Desfecho
    - **T(1)**: Tipo de estudo
    - **T(2)**: Tempo
    """)
    
    st.subheader("Exemplo:")
    st.markdown("""
    Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)
    """)

# Formulário para entrada da questão PICOTT
with st.form(key="search_form"):
    picott_text = st.text_area(
        "Insira sua questão no formato PICOTT:",
        height=100,
        help="Descreva sua questão de pesquisa seguindo a estrutura PICOTT (População, Intervenção, Comparação, Outcome, Tipo de estudo, Tempo)",
        placeholder="Ex: Pacientes adultos com diabetes tipo 2 (P) recebendo metformina (I) vs placebo (C) para redução de HbA1c (O) em ensaios clínicos randomizados (T tipo de estudo) com seguimento de 6 meses (T tempo)"
    )
    max_refinements = st.slider(
        "Número máximo de refinamentos iniciais:",
        min_value=1,
        max_value=5,
        value=3,
        help="Limite máximo de vezes que a consulta será refinada na fase inicial"
    )
    max_total_refinements = st.slider(
        "Número máximo total de refinamentos (incluindo extras):",
        min_value=3,
        max_value=10,
        value=8,
        help="Limite absoluto de refinamentos que o sistema pode realizar"
    )
    
    # Limites para decidir se a consulta está muito ampla ou restrita
    col1, col2 = st.columns(2)
    with col1:
        too_few_results = st.number_input(
            "Número mínimo de resultados desejados:",
            min_value=1,
            max_value=100,
            value=20,
            help="Se encontrar menos resultados que este valor, considerará a consulta muito restrita"
        )
    with col2:
        too_many_results = st.number_input(
            "Número máximo de resultados desejados:",
            min_value=100,
            max_value=1000,
            value=500,
            help="Se encontrar mais resultados que este valor, considerará a consulta muito ampla"
        )
        
    submit_button = st.form_submit_button(label="Pesquisar")

# Processar quando o formulário for enviado
if submit_button and picott_text:
    # Exibindo o cabeçalho dos resultados
    st.markdown("<h2 class='results-header'>Processando Pesquisa...</h2>", unsafe_allow_html=True)
    
    try:
        services = get_services()
        query_generator = services["query_generator"]
        pubmed_service = services["pubmed_service"]
        query_evaluator = services["query_evaluator"]
        
        # Cria um placeholder para cada etapa do processo
        search_progress = st.empty()
        search_progress.markdown("<div class='step-container'>Gerando consulta inicial...</div>", unsafe_allow_html=True)
        
        # Gerar consulta inicial
        with st.spinner("Gerando consulta inicial..."):
            initial_query = asyncio.run(query_generator.generate_initial_query(picott_text))
            search_progress.markdown(
                f"<div class='step-container'>✅ Consulta inicial gerada!</div>", 
                unsafe_allow_html=True
            )
            st.markdown("<h3 class='sub-header'>Consulta Inicial:</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='query-initial'>{initial_query}</div>", unsafe_allow_html=True)
        
        # Placeholder para etapas de refinamento
        refinement_steps = st.container()
        
        current_query = initial_query
        needs_refinement = True
        refinement_count = 0
        final_results = None
        last_search_results = None
        
        # Primeira fase: refinamentos iniciais
        while needs_refinement and refinement_count < max_refinements:
            with refinement_steps:
                refinement_status = st.empty()
                refinement_status.markdown(
                    f"<div class='step-container'>Buscando resultados para a consulta (Tentativa {refinement_count + 1})...</div>", 
                    unsafe_allow_html=True
                )
                
                # Realizar busca com a consulta atual
                with st.spinner(f"Buscando resultados (Tentativa {refinement_count + 1})..."):
                    search_results = asyncio.run(pubmed_service.search(current_query))
                    last_search_results = search_results
                    refinement_status.markdown(
                        f"<div class='step-container'>✅ Busca concluída! Encontrados {search_results.total_count} resultados.</div>", 
                        unsafe_allow_html=True
                    )
                
                # Avaliar resultados
                eval_status = st.empty()
                eval_status.markdown(
                    f"<div class='step-container'>Avaliando qualidade dos resultados...</div>", 
                    unsafe_allow_html=True
                )
                
                with st.spinner("Avaliando resultados..."):
                    evaluation = query_evaluator._evaluate_search_result(search_results)
                    needs_refinement = evaluation.get("issues", "") != "" and refinement_count < max_refinements
                    
                    eval_status.markdown(
                        f"<div class='step-container'>✅ Avaliação concluída! Pontuação: {evaluation['overall_score']:.2f}/1.0</div>", 
                        unsafe_allow_html=True
                    )
                    
                    # Exibir detalhes da avaliação
                    with st.expander(f"Ver detalhes da avaliação (Tentativa {refinement_count + 1})"):
                        st.json(evaluation)
                
                # Se precisa refinar, continuar o processo
                if needs_refinement and refinement_count < max_refinements:
                    refine_status = st.empty()
                    refine_status.markdown(
                        f"<div class='step-container'>Refinando consulta...</div>", 
                        unsafe_allow_html=True
                    )
                    
                    with st.spinner("Refinando consulta..."):
                        previous_query = current_query
                        refined_query = asyncio.run(query_generator.refine_query(current_query, evaluation))
                        
                        # Exibir a consulta refinada
                        st.markdown(f"<h3 class='sub-header'>Consulta Refinada (Tentativa {refinement_count + 1}):</h3>", unsafe_allow_html=True)
                        st.markdown(f"<div class='query-refined'>{refined_query}</div>", unsafe_allow_html=True)
                        
                        # Destacar as diferenças entre a consulta anterior e a refinada
                        st.markdown("<h4>Análise das mudanças:</h4>", unsafe_allow_html=True)
                        differences_html = highlight_query_differences(previous_query, refined_query)
                        st.markdown(differences_html, unsafe_allow_html=True)
                        
                        # Atualizar consulta atual para a próxima iteração
                        current_query = refined_query
                
                else:
                    final_results = search_results
            
            refinement_count += 1
        
        # Segunda fase: refinamentos extras baseados no número de resultados
        if last_search_results:
            extra_refinements_needed = 0
            
            # Verificar se o número de resultados está dentro do intervalo desejado
            if last_search_results.total_count < too_few_results:
                st.warning(f"A consulta ainda está muito restrita, com apenas {last_search_results.total_count} resultados (mínimo desejado: {too_few_results}).")
                extra_refinements_needed = min(5, max_total_refinements - refinement_count)
                st.info(f"Iniciando {extra_refinements_needed} refinamentos extras para ampliar a consulta.")
            elif last_search_results.total_count > too_many_results:
                st.warning(f"A consulta ainda está muito ampla, com {last_search_results.total_count} resultados (máximo desejado: {too_many_results}).")
                extra_refinements_needed = min(5, max_total_refinements - refinement_count)
                st.info(f"Iniciando {extra_refinements_needed} refinamentos extras para restringir a consulta.")
                
            # Realizar refinamentos extras se necessário
            for i in range(extra_refinements_needed):
                extra_iteration = refinement_count + i
                
                with refinement_steps:
                    # Calcular novo fator de avaliação específico para o tipo de problema
                    if last_search_results.total_count < too_few_results:
                        # Para consultas muito restritas, adicionar uma diretriz específica
                        evaluation["issues"] = "Consulta ainda muito restrita, necessário ampliar significativamente"
                    elif last_search_results.total_count > too_many_results:
                        # Para consultas muito amplas, adicionar uma diretriz específica
                        evaluation["issues"] = "Consulta ainda muito ampla, necessário restringir significativamente"
                    
                    # Refinar a consulta
                    refine_status = st.empty()
                    refine_status.markdown(
                        f"<div class='step-container'>Refinamento extra #{i+1}: Ajustando consulta...</div>", 
                        unsafe_allow_html=True
                    )
                    
                    with st.spinner(f"Refinamento extra #{i+1}"):
                        previous_query = current_query
                        refined_query = asyncio.run(query_generator.refine_query(current_query, evaluation))
                        
                        # Exibir a consulta refinada
                        st.markdown(f"<h3 class='sub-header'>Refinamento Extra #{i+1}:</h3>", unsafe_allow_html=True)
                        st.markdown(f"<div class='query-refined'>{refined_query}</div>", unsafe_allow_html=True)
                        
                        # Destacar as diferenças
                        st.markdown("<h4>Análise das mudanças:</h4>", unsafe_allow_html=True)
                        differences_html = highlight_query_differences(previous_query, refined_query)
                        st.markdown(differences_html, unsafe_allow_html=True)
                        
                        # Realizar busca com a consulta refinada
                        search_results = asyncio.run(pubmed_service.search(refined_query))
                        last_search_results = search_results
                        
                        # Exibir resultados
                        st.markdown(f"<div class='step-container'>✅ Busca concluída! Encontrados {search_results.total_count} resultados.</div>", unsafe_allow_html=True)
                        
                        # Avaliar se o refinamento melhorou o problema
                        if (last_search_results.total_count >= too_few_results and 
                            last_search_results.total_count <= too_many_results):
                            st.success("✅ Número de resultados agora está dentro do intervalo desejado!")
                            final_results = search_results
                            current_query = refined_query
                            break
                        
                        # Atualizar consulta e avaliação para próxima iteração
                        current_query = refined_query
                        evaluation = query_evaluator._evaluate_search_result(search_results)
                        final_results = search_results
        
        # Exibir resultados finais
        st.markdown("<h2 class='results-header'>Resultados Finais</h2>", unsafe_allow_html=True)
        
        if (refinement_count >= max_refinements and 
            ((last_search_results.total_count < too_few_results) or 
             (last_search_results.total_count > too_many_results))):
            st.warning(f"Atingido o limite máximo de refinamentos. A consulta final possui {last_search_results.total_count} resultados, que está fora do intervalo desejado ({too_few_results}-{too_many_results}).")
        
        st.markdown("<h3 class='sub-header'>Consulta Final Otimizada:</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='query-final'>{current_query}</div>", unsafe_allow_html=True)
        
        # Exibir artigos encontrados
        if final_results:
            st.markdown(f"<h3 class='sub-header'>Artigos Encontrados ({final_results.total_count} resultados):</h3>", unsafe_allow_html=True)
            
            # Verificar se temos informações de amostra para exibir
            if final_results.sample_titles and len(final_results.sample_titles) > 0:
                for i in range(len(final_results.sample_titles)):
                    title = final_results.sample_titles[i]
                    article_type = final_results.sample_types[i] if final_results.sample_types and i < len(final_results.sample_types) else "Não especificado"
                    pub_year = final_results.sample_years[i] if final_results.sample_years and i < len(final_results.sample_years) else "Não especificado"
                    pmid = final_results.ids[i] if i < len(final_results.ids) else ""
                    
                    with st.container():
                        st.markdown(f"""
                        <div class='article-preview'>
                            <h4><a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank">{title}</a></h4>
                            <p><strong>Tipo:</strong> {article_type}</p>
                            <p><strong>Ano de publicação:</strong> {pub_year}</p>
                            <p><strong>PMID:</strong> {pmid}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Se não temos detalhes dos artigos, exibimos apenas a contagem e os IDs
                st.info(f"Encontrados {final_results.total_count} resultados no PubMed. Acesse o link abaixo para visualizar os artigos completos.")
                
                # Exibir os primeiros PMIDs se disponíveis
                if final_results.ids and len(final_results.ids) > 0:
                    with st.expander("Ver PMIDs dos primeiros resultados"):
                        st.write(", ".join(final_results.ids[:20]))
                        if len(final_results.ids) > 20:
                            st.write("...")
        
        # Resumo dos resultados
        if final_results:
            st.markdown(f"""
            <div style='background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 15px 0;'>
                <h4 style='margin-top: 0;'>Resumo da Consulta</h4>
                <ul>
                    <li><strong>Total de iterações:</strong> {refinement_count}</li>
                    <li><strong>Resultados encontrados:</strong> {final_results.total_count}</li>
                    <li><strong>Intervalo desejado:</strong> {too_few_results} - {too_many_results} resultados</li>
                    <li><strong>Status:</strong> {'✅ Dentro do intervalo desejado' if too_few_results <= final_results.total_count <= too_many_results else '❌ Fora do intervalo desejado'}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar botão para copiar a consulta
        if st.button("Copiar Consulta Final", type="primary"):
            st.toast("Consulta copiada para a área de transferência!")
            st.session_state["copied_query"] = current_query
        
        # Exibir link para o PubMed
        st.markdown(f"""
        <div style='margin-top: 20px; text-align: center;'>
            <a href="https://pubmed.ncbi.nlm.nih.gov/?term={urllib.parse.quote(current_query)}" target="_blank">
                Abrir esta consulta no PubMed ↗
            </a>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar sua pesquisa: {str(e)}")
        st.exception(e)

# Rodapé
st.markdown("""
<div style='margin-top: 50px; text-align: center; color: #666;'>
    <p>Desenvolvido com ❤️ para pesquisadores e profissionais de saúde</p>
</div>
""", unsafe_allow_html=True)

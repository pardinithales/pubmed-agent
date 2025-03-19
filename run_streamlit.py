import subprocess
import os
import platform
import sys
import socket
import time
from pathlib import Path

# Obter o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

def is_port_in_use(port):
    """Verifica se uma porta está em uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_free_port(start_port=8501, max_attempts=10):
    """Encontra uma porta livre começando da porta inicial."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def is_running_on_streamlit_cloud():
    """Verifica se o código está rodando no Streamlit Cloud."""
    return os.environ.get('STREAMLIT_SHARING') == 'true' or os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app')

def main():
    print("Iniciando a interface Streamlit para pesquisa no PubMed...")
    
    # Se estiver rodando no Streamlit Cloud, sempre usar o app simplificado
    if is_running_on_streamlit_cloud():
        print("Detectado ambiente Streamlit Cloud, usando configuração de deploy...")
        
        # Caminho para o aplicativo simplificado
        simple_app_path = os.path.join(root_dir, "simple_streamlit_app.py")
        
        if os.path.exists(simple_app_path):
            try:
                # Configurar variáveis de ambiente para otimizar desempenho
                os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
                os.environ["STREAMLIT_SERVER_PORT"] = "8501"  # Forçar porta 8501
                os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5"  # Limitar tamanho de upload
                os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"  # Desativar estatísticas
                os.environ["STREAMLIT_THEME_BASE"] = "light"  # Tema mais leve
                os.environ["FORCE_SIMPLE_APP"] = "true"  # Flag para forçar app simples
                
                print("Iniciando aplicativo simplificado em modo cloud com configurações seguras...")
                import streamlit.web.cli as streamlit_cli
                sys.argv = ["streamlit", "run", simple_app_path, "--server.maxUploadSize=5"]
                streamlit_cli.main()
                
            except Exception as e:
                print(f"Erro crítico no deploy: {str(e)}")
                # Último recurso: iniciar uma página estática de erro
                with open(os.path.join(root_dir, "error.html"), "w") as f:
                    f.write("<html><body><h1>Erro no Aplicativo</h1><p>Houve um problema ao iniciar o aplicativo.</p></body></html>")
        else:
            print("ERRO: Aplicativo simplificado não encontrado!")
            # Criar um arquivo simples caso o simple_app não exista
            with open(os.path.join(root_dir, "emergency_app.py"), "w") as f:
                f.write("""
import streamlit as st
st.set_page_config(page_title="PubMed Agent - Erro", page_icon="⚠️")
st.title("⚠️ Erro de Inicialização")
st.error("O aplicativo não pôde ser iniciado corretamente.")
st.info("Este é um aplicativo de emergência criado automaticamente.")
""")
            try:
                import streamlit.web.cli as streamlit_cli
                sys.argv = ["streamlit", "run", os.path.join(root_dir, "emergency_app.py")]
                streamlit_cli.main()
            except Exception as e:
                print(f"Erro crítico final: {str(e)}")
        
        return
    
    # Para ambiente local, continuar com o comportamento normal
    # Caminho para o arquivo do aplicativo Streamlit
    streamlit_app_path = os.path.join(root_dir, "app", "frontend", "streamlit_app.py")
    
    # Caminho para o aplicativo simplificado como fallback
    simple_app_path = os.path.join(root_dir, "simple_streamlit_app.py")
    
    # Verificar se os arquivos existem
    if not os.path.exists(streamlit_app_path):
        if os.path.exists(simple_app_path):
            print(f"Aplicativo principal não encontrado. Usando versão simplificada como fallback.")
            streamlit_app_path = simple_app_path
        else:
            print(f"Erro: Nenhum aplicativo Streamlit foi encontrado.")
            return
    
    # Configuração para ambiente local
    print("Iniciando em ambiente local...")
    
    # Encontrar uma porta disponível
    port = find_free_port()
    if not port:
        print("Erro: Não foi possível encontrar uma porta disponível.")
        return
    
    print(f"Usando porta: {port}")
    
    try:
        # Comando para iniciar o Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", streamlit_app_path, f"--server.port={port}"]
        
        # Adicionar opção para abrir automaticamente no navegador
        if platform.system() != "Linux":  # No Linux, a opção de abrir navegador pode causar problemas
            cmd.append("--server.headless=false")
        
        # Executar diretamente o comando Streamlit sem capturar a saída
        # Isso mantém o processo Streamlit ativo e visível no terminal
        print("Executando Streamlit. Pressione Ctrl+C para interromper.")
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"Erro ao iniciar o Streamlit: {str(e)}")

if __name__ == "__main__":
    main()

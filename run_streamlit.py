import subprocess
import os
import platform
import sys
import socket
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
    
    # Caminho para o arquivo do aplicativo Streamlit
    streamlit_app_path = os.path.join(root_dir, "app", "frontend", "streamlit_app.py")
    
    # Verificar se o arquivo existe
    if not os.path.exists(streamlit_app_path):
        print(f"Erro: O arquivo {streamlit_app_path} não foi encontrado.")
        return
    
    # Se estiver rodando no Streamlit Cloud, o serviço será gerenciado automaticamente
    if is_running_on_streamlit_cloud():
        print("Detectado ambiente Streamlit Cloud, usando configuração de deploy...")
        import streamlit.web.cli as streamlit_cli
        sys.argv = ["streamlit", "run", streamlit_app_path]
        streamlit_cli.main()
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

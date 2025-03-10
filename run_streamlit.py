import subprocess
import os
import platform
import sys
from pathlib import Path

# Obter o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

def main():
    print("Iniciando a interface Streamlit para pesquisa no PubMed...")
    
    # Caminho para o arquivo do aplicativo Streamlit
    streamlit_app_path = os.path.join(root_dir, "app", "frontend", "streamlit_app.py")
    
    # Verificar se o arquivo existe
    if not os.path.exists(streamlit_app_path):
        print(f"Erro: O arquivo {streamlit_app_path} não foi encontrado.")
        return
    
    try:
        # Comando para iniciar o Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", streamlit_app_path, "--server.port=8501"]
        
        # Adicionar opção para abrir automaticamente no navegador
        if platform.system() != "Linux":  # No Linux, a opção de abrir navegador pode causar problemas
            cmd.append("--server.headless=false")
        
        # Executar o comando
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Imprimir a saída em tempo real
        for line in process.stdout:
            print(line, end='')
        
    except Exception as e:
        print(f"Erro ao iniciar o Streamlit: {str(e)}")

if __name__ == "__main__":
    main()

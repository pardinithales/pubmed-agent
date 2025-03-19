#!/usr/bin/env python3
"""
Script de inicialização para ambiente local.
Este script permite executar o aplicativo Streamlit conectando-se a uma API local ou remota.
"""
import subprocess
import os
import sys
import platform
import time
import argparse
from pathlib import Path

# Obter o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

def parse_arguments():
    """Parse os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Inicia o PubMed Agent localmente ou com API remota")
    
    parser.add_argument(
        "--api", 
        choices=["local", "remote"], 
        default="local",
        help="Escolha entre usar API local ou remota (Vercel)"
    )
    
    parser.add_argument(
        "--url", 
        type=str, 
        default="https://pubmed-search-api.vercel.app",
        help="URL da API remota (usado apenas com --api=remote)"
    )
    
    return parser.parse_args()

def start_local_api():
    """Inicia a API localmente usando uvicorn."""
    print("Iniciando API local na porta 8000...")
    
    # Comando para iniciar a API
    if platform.system() == "Windows":
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            preexec_fn=os.setpgrp
        )
    
    # Aguardar um pouco para a API iniciar
    time.sleep(2)
    
    print("API local iniciada. Pressione Ctrl+C para encerrar quando terminar.")
    return api_process

def start_streamlit(api_url=None):
    """Inicia a interface Streamlit."""
    # Definir caminho do app
    app_path = os.path.join(root_dir, "streamlit_app.py")
    
    # Se API remota, definir variável de ambiente com URL
    env = os.environ.copy()
    if api_url:
        env["API_URL"] = api_url
        print(f"Usando API remota: {api_url}")
    
    print(f"Iniciando interface Streamlit...")
    
    # Comando para iniciar o Streamlit
    if platform.system() == "Windows":
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=false"],
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=false"],
            env=env,
            preexec_fn=os.setpgrp
        )
    
    return streamlit_process

def main():
    """Função principal."""
    args = parse_arguments()
    
    print("\n=== Iniciando PubMed Agent ===\n")
    
    api_process = None
    
    # Iniciar API local se necessário
    if args.api == "local":
        api_process = start_local_api()
        api_url = "http://localhost:8000"
    else:
        print(f"Usando API remota: {args.url}")
        api_url = args.url
    
    # Iniciar Streamlit
    streamlit_process = start_streamlit(api_url)
    
    try:
        # Manter o programa em execução
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Encerrar processos ao pressionar Ctrl+C
        print("\nEncerrando aplicação...")
        
        if streamlit_process:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(streamlit_process.pid)])
            else:
                streamlit_process.terminate()
        
        if api_process:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(api_process.pid)])
            else:
                api_process.terminate()
        
        print("Aplicação encerrada.")

if __name__ == "__main__":
    main() 
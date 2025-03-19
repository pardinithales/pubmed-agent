#!/usr/bin/env python3
"""
Script de inicialização unificado para o Agente de Busca PubMed.
Este script inicia tanto a API FastAPI quanto a interface Streamlit.
"""
import subprocess
import os
import sys
import platform
import time
import atexit
import socket
from pathlib import Path

# Obter o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

# Configurações
API_PORT = 8000
STREAMLIT_PORT = 8501
MAX_WAIT_TIME = 30  # segundos para aguardar a API iniciar

def is_port_in_use(port):
    """Verifica se uma porta está em uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_api(port=API_PORT, max_wait_time=MAX_WAIT_TIME):
    """Aguarda até que a API esteja disponível."""
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
        sys.stdout.write(".")
        sys.stdout.flush()
    return False

def start_fastapi():
    """Inicia o servidor FastAPI em segundo plano."""
    # Verifica se a API já está rodando
    if is_port_in_use(API_PORT):
        print(f"✅ API já está rodando na porta {API_PORT}")
        return None
    
    print(f"Iniciando API FastAPI na porta {API_PORT}...")
    
    # Comando para iniciar o servidor FastAPI
    if platform.system() == "Windows":
        # No Windows
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(API_PORT)],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Em outros sistemas operacionais
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(API_PORT)],
            preexec_fn=os.setpgrp
        )
    
    # Aguarda API iniciar
    print("Aguardando API iniciar", end="")
    if wait_for_api():
        print(f"\n✅ API iniciada com sucesso na porta {API_PORT}")
    else:
        print(f"\n⚠️ Não foi possível confirmar que a API está rodando. Continuando mesmo assim...")
    
    return api_process

def start_streamlit():
    """Inicia a interface Streamlit."""
    # Verifica se o Streamlit já está rodando
    if is_port_in_use(STREAMLIT_PORT):
        print(f"⚠️ Aviso: Já existe um processo rodando na porta {STREAMLIT_PORT}")
        print("O Streamlit será iniciado em uma porta diferente.")
    
    # Caminho para o arquivo do aplicativo Streamlit
    streamlit_app_path = os.path.join(root_dir, "app", "frontend", "streamlit_app.py")
    
    # Caminho para o aplicativo simplificado como fallback
    simple_app_path = os.path.join(root_dir, "simple_streamlit_app.py")
    
    # Verificar qual aplicativo existe
    if os.path.exists(streamlit_app_path):
        app_path = streamlit_app_path
        print("Usando aplicativo Streamlit completo")
    elif os.path.exists(simple_app_path):
        app_path = simple_app_path
        print("Usando aplicativo Streamlit simplificado (fallback)")
    else:
        print("❌ Erro: Nenhum aplicativo Streamlit foi encontrado.")
        return None
    
    print(f"Iniciando interface Streamlit...")
    
    # Comando para iniciar o Streamlit
    if platform.system() == "Windows":
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=false"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        streamlit_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=false"],
            preexec_fn=os.setpgrp
        )
    
    return streamlit_process

def register_cleanup(processes):
    """Registra funções para limpeza dos processos ao encerrar."""
    def cleanup():
        for process in processes:
            if process:
                try:
                    if platform.system() == "Windows":
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])
                    else:
                        process.terminate()
                except Exception as e:
                    print(f"Erro ao encerrar processo: {e}")
    
    atexit.register(cleanup)

def main():
    """Função principal que inicia o Agente de Busca PubMed."""
    print("\n=== Iniciando Agente de Busca PubMed ===\n")
    
    # Lista para armazenar processos iniciados
    processes = []
    
    # Inicia a API
    api_process = start_fastapi()
    if api_process:
        processes.append(api_process)
    
    # Pequena pausa para garantir que a API esteja estável
    time.sleep(1)
    
    # Inicia o Streamlit
    streamlit_process = start_streamlit()
    if streamlit_process:
        processes.append(streamlit_process)
    
    # Registra função para encerrar processos quando o programa principal terminar
    register_cleanup(processes)
    
    print("\n✅ Agente de Busca PubMed iniciado com sucesso!")
    print(f"   * API: http://localhost:{API_PORT}")
    print(f"   * Interface: http://localhost:{STREAMLIT_PORT}")
    print("\nPressione Ctrl+C para encerrar todos os serviços\n")
    
    try:
        # Mantém o programa principal em execução até que o usuário interrompa
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando Agente de Busca PubMed...")

if __name__ == "__main__":
    main() 

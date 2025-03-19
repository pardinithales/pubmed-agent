#!/usr/bin/env python3
"""
Script de configuração para ambiente Streamlit Cloud.
Este script deve ser executado automaticamente no Streamlit Cloud para configurar o ambiente.

O Streamlit Cloud executa este arquivo se estiver presente no diretório raiz.
"""
import os
import sys
import subprocess
import importlib
from pathlib import Path

# Obter o diretório raiz do projeto
root_dir = Path(__file__).resolve().parent

def check_environment():
    """Verifica se estamos rodando no Streamlit Cloud."""
    is_cloud = os.environ.get('STREAMLIT_SHARING') == 'true' or os.environ.get('STREAMLIT_SERVER_URL', '').endswith('streamlit.app')
    print(f"Ambiente Streamlit Cloud: {is_cloud}")
    return is_cloud

def install_dependencies():
    """Instala todas as dependências necessárias."""
    print("Instalando dependências do projeto...")
    
    # Verificar se o arquivo requirements.txt existe
    req_path = os.path.join(root_dir, "requirements.txt")
    if not os.path.exists(req_path):
        print("❌ Arquivo requirements.txt não encontrado!")
        return False
    
    # Instalar dependências do requirements.txt
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", req_path
        ])
        print("✅ Dependências do requirements.txt instaladas com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências do requirements.txt: {e}")
        return False
    
    # Garantir que pydantic-settings esteja instalado
    try:
        importlib.import_module("pydantic_settings")
        print("✅ Módulo pydantic_settings está instalado!")
    except ImportError:
        print("Instalando pydantic-settings...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "pydantic-settings>=2.1.0"
            ])
            print("✅ pydantic-settings instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar pydantic-settings: {e}")
            return False
    
    return True

def setup_cloud_environment():
    """Configura o ambiente para o Streamlit Cloud."""
    print("Configurando ambiente para Streamlit Cloud...")
    
    # Definir variáveis de ambiente específicas para o Cloud
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5"  # Limitar tamanho de upload
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"  # Desativar estatísticas
    os.environ["STREAMLIT_THEME_BASE"] = "light"  # Tema mais leve
    os.environ["FORCE_SIMPLE_APP"] = "true"  # Flag para forçar app simples
    
    print("✅ Variáveis de ambiente configuradas com sucesso!")
    return True

def main():
    """Função principal do script de configuração."""
    print("\n=== Configurando Ambiente para Aplicativo PubMed ===\n")
    
    # Verificar se estamos no Streamlit Cloud
    is_cloud = check_environment()
    if not is_cloud:
        print("Este script deve ser executado apenas no ambiente Streamlit Cloud.")
        print("Para ambiente local, use 'python start_pubmed_agent.py'.")
        return
    
    # Instalar dependências
    if not install_dependencies():
        print("❌ Não foi possível instalar todas as dependências necessárias.")
        return
    
    # Configurar ambiente Cloud
    if not setup_cloud_environment():
        print("❌ Não foi possível configurar o ambiente corretamente.")
        return
    
    print("\n✅ Configuração do ambiente Streamlit Cloud concluída com sucesso!")
    print("   O aplicativo está pronto para ser iniciado.")

if __name__ == "__main__":
    main() 
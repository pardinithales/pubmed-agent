import os
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente
    """
    # Configurações de API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Agente de Busca Otimizada para PubMed"
    
    # Configurações de segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    
    # Chaves de API para LLMs
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Configurações do PubMed
    PUBMED_EMAIL: str = os.getenv("PUBMED_EMAIL", "user@example.com")
    
    # Configurações de log
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Configurações de saída
    DEFAULT_MAX_OUTPUT_TOKENS: int = int(os.getenv("DEFAULT_MAX_OUTPUT_TOKENS", "4000"))
    
    # Configurações de banco de dados
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # Configurações do servidor
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Ambiente (desenvolvimento, teste, produção)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instância global das configurações
settings = Settings()

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

def get_logger(name: str) -> logging.Logger:
    """
    Configura e retorna um logger formatado para o módulo especificado.
    
    Args:
        name: Nome do módulo para o qual criar o logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    # Cria o diretório de logs se não existir
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configura o logger
    logger = logging.getLogger(name)
    
    # Define o nível de log baseado nas configurações
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logger.setLevel(log_level)
    
    # Limpa handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers.clear()
    
    # Formata as mensagens de log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        logs_dir / "pubmed_agent.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    return logger

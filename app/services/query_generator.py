import os
import json
import asyncio
from typing import Dict, List, Optional, Any

import httpx
from fastapi import HTTPException

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class QueryGenerator:
    """
    Serviço responsável por gerar consultas PubMed otimizadas a partir de
    perguntas clínicas no formato PICOTT, utilizando LLMs.
    """
    
    def __init__(self):
        """
        Inicializa o gerador de consultas com as configurações necessárias
        para as APIs dos modelos de linguagem.
        """
        self.deepseek_api_key = settings.DEEPSEEK_API_KEY
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        self.openai_api_key = settings.OPENAI_API_KEY
        self.timeout = 60.0  # timeout em segundos
        
        # Prompt base para a geração da consulta inicial
        self.initial_query_prompt = """
        Você é um especialista em pesquisa científica biomédica com amplo conhecimento em metodologia de busca bibliográfica no PubMed.
        
        Sua tarefa é analisar uma pergunta clínica no formato PICOTT (População, Intervenção, Comparação, Outcome, Tipo de estudo, Tempo) e transformá-la em uma consulta otimizada para o PubMed.
        
        REGRAS IMPORTANTES:
        1. Utilize APENAS qualificadores [tiab] (título/resumo) para cada termo
        2. Use operadores booleanos (AND, OR) adequadamente
        3. Agrupe termos relacionados com parênteses
        4. Inclua sinônimos importantes para cada conceito
        5. NÃO use termos MeSH nesta etapa inicial
        6. NÃO use filtros como "Humans" ou limites de data
        7. Mantenha a consulta focada nos elementos PICOTT fornecidos
        
        FORMATO DE RESPOSTA:
        Retorne APENAS a string da consulta PubMed, sem explicações ou texto adicional.
        
        PERGUNTA CLÍNICA (PICOTT):
        {picott_text}
        """
    
    async def generate_initial_query(self, picott_text: str) -> str:
        """
        Gera uma consulta inicial para o PubMed baseada na pergunta PICOTT.
        Utiliza a API DeepSeek para maior precisão na geração da consulta.
        
        Args:
            picott_text: Texto da pergunta clínica no formato PICOTT
            
        Returns:
            str: Consulta PubMed formatada com operadores booleanos e qualificadores [tiab]
        """
        logger.info("Gerando consulta inicial baseada na pergunta PICOTT")
        
        try:
            # Prepara o prompt com a pergunta do usuário
            prompt = self.initial_query_prompt.format(picott_text=picott_text)
            
            # Se a chave da API DeepSeek estiver disponível, usa essa API
            if self.deepseek_api_key:
                return await self._generate_with_deepseek(prompt)
            # Como fallback, usa a API da OpenAI
            elif self.openai_api_key:
                return await self._generate_with_openai(prompt)
            # Se nenhuma API estiver disponível, lança um erro
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Nenhuma API de LLM configurada. Verifique as variáveis de ambiente."
                )
                
        except Exception as e:
            logger.error(f"Erro ao gerar consulta inicial: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar consulta inicial: {str(e)}"
            )
    
    async def refine_query(self, current_query: str, evaluation_results: Dict[str, Any]) -> str:
        """
        Refina uma consulta existente com base nos resultados da avaliação.
        
        Args:
            current_query: Consulta atual do PubMed
            evaluation_results: Resultados da avaliação da consulta
            
        Returns:
            str: Consulta PubMed refinada
        """
        logger.info(f"Iniciando refinamento da consulta: {current_query}")
        logger.info(f"Resultados da avaliação: {json.dumps(evaluation_results, indent=2)}")
        
        # Verifica número total de resultados
        total_results = evaluation_results.get('total_count', 0)
        
        refinement_prompt = f"""
        Você é um especialista em pesquisa científica biomédica com amplo conhecimento em metodologia de busca bibliográfica no PubMed.
        
        Sua tarefa é refinar SIGNIFICATIVAMENTE uma consulta PubMed existente com base nos resultados obtidos e nas métricas de avaliação.
        
        CONSULTA ATUAL:
        {current_query}
        
        RESULTADOS DA AVALIAÇÃO:
        - Total de resultados: {evaluation_results.get('total_count', 0)}
        - Proporção de estudos primários: {evaluation_results.get('primary_studies_ratio', 0)}
        - Proporção de revisões sistemáticas: {evaluation_results.get('systematic_reviews_ratio', 0)}
        - Relevância média: {evaluation_results.get('average_relevance', 0)}
        
        PROBLEMAS IDENTIFICADOS:
        {evaluation_results.get('issues', 'Nenhum problema específico identificado')}
        
        DIRETRIZES GERAIS:
        - SEMPRE priorize os elementos de POPULAÇÃO e INTERVENÇÃO em suas refinamentos
        - Toda consulta deve manter esses elementos básicos bem definidos, mesmo que seja necessário remover outros aspectos
        
        DIRETRIZES PARA REFINAMENTO:
        1. Faça alterações SUBSTANCIAIS na consulta atual - não apenas mudanças pequenas
        
        2. TERMOS PROIBIDOS - NUNCA inclua estes termos extremamente genéricos que geram milhões de resultados:
           - "study"[tiab]
           - "research"[tiab]
           - "patients"[tiab] (use termos específicos da população como "diabetic patients", "hypertensive patients", etc.)
           - "results"[tiab]
           - "effects"[tiab]
           - "treatment"[tiab] (a menos que seja um termo específico do tratamento)
           - "evidence"[tiab]
           - "data"[tiab]
           - Termos genéricos para população como "subjects", "individuals", "participants" sem qualificadores
        
        3. POPULAÇÃO - SEMPRE priorize e mantenha:
           - Termos específicos para a população de estudo
           - Variações de idade se relevante ("elderly", "pediatric", "children", "adolescents", etc.)
           - Condições associadas à população ("diabetic", "hypertensive", "obese", etc.)
           - Adicione pelo menos 2-3 sinônimos específicos para a população

        4. INTERVENÇÃO - SEMPRE priorize e mantenha:
           - Nome(s) da(s) intervenção(ões) principal(is)
           - IMPORTANTE: Se envolve medicamentos, SEMPRE adicione os nomes comerciais relevantes
             (Ex: metformina → adicione "Glucophage", "Fortamet", "Glumetza", "Riomet")
           - Adicione sinônimos e termos relacionados à intervenção
           - Se aplicável, especifique a via de administração ou forma farmacêutica

        5. Se há poucos resultados (menos de 50), torne a consulta mais ampla:
           - MANTENHA os termos principais de população e intervenção, mas REMOVA:
           - Termos relacionados a desfechos (outcomes) específicos
           - Especificações de tempo
           - Termos de comparação (placebo, controle, etc.)
           - Qualificadores restritivos como "severe", "advanced", "resistant", etc.
           
        6. Se há muitos resultados (mais de 300):
           - MANTENHA os termos principais de população e intervenção
           - ADICIONE mais especificações de desfechos (outcomes)
           - ADICIONE especificações de tempo se relevante
           - Use aspas para frases exatas nos termos de população e intervenção
           - Adicione qualificadores adicionais para focar melhor
           
        7. Se a relevância está baixa:
           - MANTENHA a estrutura principal de população e intervenção
           - Refine os termos de população para serem mais específicos
           - Adicione nomes comerciais de medicamentos se ainda não estiverem presentes
           - Substitua termos menos relevantes por alternativas mais focadas
           
        8. VERIFICAÇÃO FINAL - CRITÉRIOS DE QUALIDADE:
           - População e intervenção DEVEM estar claramente presentes e serem a parte mais forte da consulta
           - Para medicamentos, verifique se pelo menos um nome comercial está incluído
           - Evite termos genéricos para população sem qualificadores específicos
           - Use no máximo 5 sinônimos para cada conceito principal
           - NUNCA use termos extremamente genéricos listados acima
           - Se a consulta anterior tinha menos de 20 resultados, certifique-se de REMOVER termos de outcome e tempo
           - Se a consulta anterior tinha mais de 500 resultados, certifique-se de ADICIONAR termos específicos de outcome e tempo
        
        9. IMPORTANTE: Suas alterações devem ser significativas o suficiente para mudar pelo menos 30% dos resultados
        
        FORMATO DE RESPOSTA:
        Retorne APENAS a string da consulta PubMed refinada, sem explicações ou texto adicional.
        """
        
        try:
            # Se a chave da API DeepSeek estiver disponível, usa essa API
            if self.deepseek_api_key:
                return await self._generate_with_deepseek(refinement_prompt)
            # Como fallback, usa a API da OpenAI
            elif self.openai_api_key:
                return await self._generate_with_openai(refinement_prompt)
            # Se nenhuma API estiver disponível, lança um erro
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Nenhuma API de LLM configurada. Verifique as variáveis de ambiente."
                )
                
        except Exception as e:
            logger.error(f"Erro ao refinar consulta: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao refinar consulta: {str(e)}"
            )
    
    async def _generate_with_deepseek(self, prompt: str) -> str:
        """
        Gera texto usando a API DeepSeek.
        
        Args:
            prompt: Texto do prompt para a API
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em pesquisa biomédica."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """
        Gera texto usando a API OpenAI como fallback.
        
        Args:
            prompt: Texto do prompt para a API
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.openai_api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em pesquisa biomédica."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()

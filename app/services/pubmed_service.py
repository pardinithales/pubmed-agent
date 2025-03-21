import os
import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote_plus
import random

import httpx
from fastapi import HTTPException

from app.models.schemas import PubMedSearchResult, ArticleMetadata
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PubMedService:
    """
    Serviço para interação com a API do PubMed (NCBI E-utilities)
    """
    
    def __init__(self):
        """Inicializa o serviço PubMed com URLs base e timeouts apropriados"""
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.esearch_url = f"{self.base_url}/esearch.fcgi"
        self.efetch_url = f"{self.base_url}/efetch.fcgi"
        self.esummary_url = f"{self.base_url}/esummary.fcgi"
        self.timeout = 30.0  # timeout em segundos
        
        # Parâmetros comuns para todas as requisições
        self.common_params = {
            "db": "pubmed",
            "retmode": "xml",
            "tool": "PubMedSearchAgent",
            "email": os.getenv("PUBMED_EMAIL", "user@example.com")
        }
    
    async def search(self, query: str, max_results: int = 20) -> PubMedSearchResult:
        """
        Realiza uma busca no PubMed usando a consulta fornecida
        
        Args:
            query: String de consulta formatada para o PubMed
            max_results: Número máximo de resultados a retornar
            
        Returns:
            PubMedSearchResult: Resultado da busca com contagem e IDs
        """
        logger.info(f"Realizando busca no PubMed: {query}")
        
        try:
            # Parâmetros para a requisição de busca
            search_params = {
                **self.common_params,
                "term": query,
                "retmax": max_results,
                "usehistory": "y"
            }
            
            # Faz a requisição para o endpoint de busca
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.esearch_url, params=search_params)
                response.raise_for_status()
            
            # Processa o XML da resposta
            root = ET.fromstring(response.text)
            
            # Extrai a contagem total de resultados
            count_elem = root.find(".//Count")
            total_count = int(count_elem.text) if count_elem is not None else 0
            
            # Extrai os IDs dos artigos encontrados
            id_elements = root.findall(".//IdList/Id")
            ids = [elem.text for elem in id_elements]
            
            # Se nenhum resultado for encontrado, retorna um resultado vazio
            if not ids:
                return PubMedSearchResult(
                    query=query,
                    total_count=0,
                    ids=[]
                )
            
            # Busca metadados para uma amostra dos artigos encontrados
            if ids and total_count > 0:
                metadata = await self._get_articles_metadata(ids[:min(5, len(ids))])
                
                sample_titles = [article.title for article in metadata]
                sample_types = [", ".join(article.publication_type) for article in metadata]
                sample_years = [article.publication_year for article in metadata]
            else:
                sample_titles = []
                sample_types = []
                sample_years = []
            
            # Cria e retorna o objeto de resultado
            return PubMedSearchResult(
                query=query,
                total_count=total_count,
                ids=ids,
                sample_titles=sample_titles,
                sample_types=sample_types,
                sample_years=sample_years
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar no PubMed: {str(e)}")
            raise HTTPException(status_code=e.response.status_code, 
                               detail=f"Erro na API do PubMed: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão com a API do PubMed: {str(e)}")
            raise HTTPException(status_code=503, 
                               detail=f"Erro de conexão com a API do PubMed: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao processar busca no PubMed: {str(e)}")
            raise HTTPException(status_code=500, 
                               detail=f"Erro ao processar busca no PubMed: {str(e)}")
    
    async def _get_articles_metadata(self, pmids: List[str]) -> List[ArticleMetadata]:
        """
        Obtém metadados de artigos específicos usando seus PMIDs
        
        Args:
            pmids: Lista de PMIDs dos artigos
            
        Returns:
            List[ArticleMetadata]: Lista de metadados dos artigos
        """
        if not pmids:
            return []
        
        try:
            # Parâmetros para a requisição de resumo
            summary_params = {
                **self.common_params,
                "id": ",".join(pmids),
                "retmode": "xml"
            }
            
            # Faz a requisição para o endpoint de resumo
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.esummary_url, params=summary_params)
                response.raise_for_status()
            
            # Processa o XML da resposta
            root = ET.fromstring(response.text)
            
            metadata_list = []
            for doc_sum in root.findall(".//DocSum"):
                pmid = doc_sum.find("Id").text
                
                # Extrai informações dos elementos Item
                title = ""
                pub_types = []
                pub_year = ""
                
                for item in doc_sum.findall(".//Item"):
                    if item.attrib.get("Name") == "Title":
                        title = item.text or ""
                    elif item.attrib.get("Name") == "PubTypeList":
                        for pub_type in item.findall(".//Item"):
                            if pub_type.text:
                                pub_types.append(pub_type.text)
                    elif item.attrib.get("Name") == "PubDate":
                        pub_date = item.text or ""
                        # Extrai apenas o ano da data de publicação
                        pub_year = pub_date.split()[0] if pub_date else ""
                
                # Cria o objeto de metadados
                metadata = ArticleMetadata(
                    pmid=pmid,
                    title=title,
                    publication_type=pub_types if pub_types else ["Unknown"],
                    publication_year=pub_year if pub_year else "Unknown",
                    abstract=None  # Não disponível no eSummary
                )
                
                metadata_list.append(metadata)
            
            return metadata_list
            
        except Exception as e:
            logger.error(f"Erro ao obter metadados dos artigos: {str(e)}")
            return []
    
    async def perform_web_scraping_search(self, query: str) -> PubMedSearchResult:
        """
        Alternativa de busca usando web scraping quando a API apresenta problemas.
        Esta é uma implementação simplificada que pode ser expandida conforme necessidade.
        
        Args:
            query: String de consulta formatada para o PubMed
            
        Returns:
            PubMedSearchResult: Resultado da busca com contagem e IDs
        """
        logger.info(f"Realizando busca via web scraping: {query}")
        
        try:
            # URL do PubMed para busca web
            encoded_query = quote_plus(query)
            url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_query}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Aqui seria necessário implementar um parser HTML para extrair os resultados
            # Este é um placeholder para a lógica de scraping
            # Usando BeautifulSoup ou outra biblioteca de parsing HTML
            
            # Por enquanto, retornamos dados de exemplo
            return PubMedSearchResult(
                query=query,
                total_count=0,  # Seria extraído do HTML
                ids=[],        # Seria extraído do HTML
                sample_titles=[],
                sample_types=[],
                sample_years=[]
            )
            
        except Exception as e:
            logger.error(f"Erro ao realizar web scraping: {str(e)}")
            raise HTTPException(status_code=500, 
                               detail=f"Erro ao realizar web scraping do PubMed: {str(e)}")
    
    async def get_article_abstracts(self, pmids: List[str], sample_size: int = 10) -> List[Dict[str, str]]:
        """
        Obtém abstracts de artigos a partir de seus PMIDs
        
        Args:
            pmids: Lista de PMIDs dos artigos
            sample_size: Número de artigos para amostrar (se houver mais que sample_size PMIDs)
            
        Returns:
            List[Dict[str, str]]: Lista de dicionários com PMID, título e abstract
        """
        if not pmids:
            return []
        
        # Se houver mais PMIDs que o tamanho da amostra, seleciona aleatoriamente
        if len(pmids) > sample_size:
            selected_pmids = random.sample(pmids, sample_size)
        else:
            selected_pmids = pmids
            
        logger.info(f"Obtendo abstracts para {len(selected_pmids)} artigos")
        
        try:
            # Parâmetros para a requisição de fetch
            fetch_params = {
                **self.common_params,
                "id": ",".join(selected_pmids),
                "retmode": "xml",
                "rettype": "abstract"
            }
            
            # Faz a requisição para o endpoint de fetch
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.efetch_url, params=fetch_params)
                response.raise_for_status()
            
            # Processa o XML da resposta
            root = ET.fromstring(response.text)
            
            abstracts = []
            
            # Processa cada artigo no XML
            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "Unknown"
                
                # Busca o título
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "No title available"
                
                # Busca o abstract - pode estar em vários formatos
                abstract_text = ""
                
                # Primeiro tenta encontrar abstract na forma de AbstractText
                abstract_elems = article.findall(".//Abstract/AbstractText")
                if abstract_elems:
                    for abstract_elem in abstract_elems:
                        # Verifica se tem Label (seções do abstract)
                        label = abstract_elem.get("Label", "")
                        if label:
                            abstract_text += f"{label}: {abstract_elem.text}\n"
                        else:
                            abstract_text += f"{abstract_elem.text}\n"
                else:
                    # Tenta outros formatos comuns
                    other_abstract = article.find(".//Abstract//text")
                    if other_abstract is not None and other_abstract.text:
                        abstract_text = other_abstract.text
                
                # Se não encontrou abstract
                if not abstract_text:
                    abstract_text = "Abstract not available"
                
                abstracts.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract_text.strip()
                })
            
            return abstracts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar abstracts no PubMed: {str(e)}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão ao buscar abstracts na API do PubMed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Erro ao processar abstracts do PubMed: {str(e)}")
            return []

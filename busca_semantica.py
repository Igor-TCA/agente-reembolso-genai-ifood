"""
Sistema de Busca Semântica para Base de Conhecimento.
Implementa busca por similaridade usando TF-IDF e embeddings.
"""
import csv
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ItemConhecimento:
    """Representa um item da base de conhecimento."""
    categoria: str
    pergunta: str
    resposta: str
    fonte: str
    embedding: List[float] = None
    
    def __post_init__(self):
        if self.embedding is None:
            self.embedding = []


@dataclass
class ResultadoBusca:
    """Resultado de uma busca semântica."""
    item: ItemConhecimento
    score_similaridade: float
    metodo_match: str  # "exato", "tfidf", "semantico"
    
    def __repr__(self):
        return f"ResultadoBusca(fonte={self.item.fonte}, score={self.score_similaridade:.3f})"


class ProcessadorTexto:
    """Processador de texto para normalização e tokenização."""
    
    # Stopwords em português
    STOPWORDS = {
        'a', 'o', 'e', 'de', 'da', 'do', 'em', 'um', 'uma', 'para', 'com',
        'não', 'que', 'se', 'na', 'no', 'os', 'as', 'por', 'mais', 'foi',
        'como', 'mas', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou',
        'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também',
        'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois',
        'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem', 'nas', 'me', 'esse',
        'eles', 'estão', 'você', 'tinha', 'foram', 'essa', 'num', 'nem',
        'suas', 'meu', 'minha', 'têm', 'numa', 'pelos', 'elas', 'havia',
        'seja', 'qual', 'será', 'nós', 'tenho', 'lhe', 'deles', 'essas',
        'esses', 'pelas', 'este', 'fosse', 'dele', 'tu', 'te', 'vocês'
    }
    
    # Sinônimos comuns no contexto de reembolso
    SINONIMOS = {
        'cancelar': ['cancelamento', 'desistir', 'desistência', 'anular'],
        'reembolso': ['reembolsar', 'devolução', 'devolver', 'estorno', 'estornar'],
        'erro': ['errado', 'incorreto', 'falha', 'problema', 'defeito'],
        'pedido': ['compra', 'ordem', 'encomenda'],
        'entrega': ['entregar', 'entregue', 'chegou', 'recebido', 'receber'],
        'cobrado': ['cobrança', 'cobrar', 'pago', 'pagamento', 'valor'],
        'atraso': ['atrasado', 'demorou', 'demora', 'lento'],
        'fraude': ['fraudulento', 'suspeito', 'invadido', 'hackeado'],
        'duplicado': ['duplicada', 'duas vezes', 'dobrado', 'repetido']
    }
    
    @classmethod
    def normalizar(cls, texto: str) -> str:
        """Normaliza texto para comparação."""
        texto = texto.lower()
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    @classmethod
    def tokenizar(cls, texto: str, remover_stopwords: bool = True) -> List[str]:
        """Tokeniza texto em palavras."""
        texto_normalizado = cls.normalizar(texto)
        tokens = texto_normalizado.split()
        
        if remover_stopwords:
            tokens = [t for t in tokens if t not in cls.STOPWORDS and len(t) > 2]
        
        return tokens
    
    @classmethod
    def expandir_sinonimos(cls, tokens: List[str]) -> List[str]:
        """Expande tokens com seus sinônimos."""
        tokens_expandidos = set(tokens)
        
        for token in tokens:
            # Buscar sinônimos diretos
            if token in cls.SINONIMOS:
                tokens_expandidos.update(cls.SINONIMOS[token])
            
            # Buscar se o token é sinônimo de outra palavra
            for palavra_base, sinonimos in cls.SINONIMOS.items():
                if token in sinonimos:
                    tokens_expandidos.add(palavra_base)
                    tokens_expandidos.update(sinonimos)
        
        return list(tokens_expandidos)


class MotorTFIDF:
    """Motor de busca usando TF-IDF."""
    
    def __init__(self):
        self.vocabulario: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.documentos_tfidf: List[Dict[str, float]] = []
        self.num_documentos: int = 0
    
    def construir_indice(self, documentos: List[str]):
        """Constrói índice TF-IDF a partir de documentos."""
        self.num_documentos = len(documentos)
        
        # Contar frequência de documento para cada termo
        df = Counter()
        documentos_tokens = []
        
        for doc in documentos:
            tokens = ProcessadorTexto.tokenizar(doc)
            documentos_tokens.append(tokens)
            tokens_unicos = set(tokens)
            for token in tokens_unicos:
                df[token] += 1
                if token not in self.vocabulario:
                    self.vocabulario[token] = len(self.vocabulario)
        
        # Calcular IDF
        for termo, freq_doc in df.items():
            self.idf[termo] = math.log(self.num_documentos / (1 + freq_doc))
        
        # Calcular TF-IDF para cada documento
        for tokens in documentos_tokens:
            tf = Counter(tokens)
            tfidf = {}
            for termo, freq in tf.items():
                tf_norm = freq / len(tokens) if tokens else 0
                tfidf[termo] = tf_norm * self.idf.get(termo, 0)
            self.documentos_tfidf.append(tfidf)
    
    def calcular_similaridade(self, consulta: str, idx_documento: int) -> float:
        """Calcula similaridade coseno entre consulta e documento."""
        tokens_consulta = ProcessadorTexto.tokenizar(consulta)
        tokens_expandidos = ProcessadorTexto.expandir_sinonimos(tokens_consulta)
        
        # TF-IDF da consulta
        tf_consulta = Counter(tokens_expandidos)
        tfidf_consulta = {}
        for termo, freq in tf_consulta.items():
            tf_norm = freq / len(tokens_expandidos) if tokens_expandidos else 0
            tfidf_consulta[termo] = tf_norm * self.idf.get(termo, 0)
        
        # Similaridade coseno
        doc_tfidf = self.documentos_tfidf[idx_documento]
        
        dot_product = sum(
            tfidf_consulta.get(termo, 0) * doc_tfidf.get(termo, 0)
            for termo in set(tfidf_consulta.keys()) | set(doc_tfidf.keys())
        )
        
        norm_consulta = math.sqrt(sum(v**2 for v in tfidf_consulta.values()))
        norm_doc = math.sqrt(sum(v**2 for v in doc_tfidf.values()))
        
        if norm_consulta == 0 or norm_doc == 0:
            return 0.0
        
        return dot_product / (norm_consulta * norm_doc)


class BaseConhecimentoSemantica:
    """
    Base de conhecimento com busca semântica.
    Combina busca exata, TF-IDF e expansão de sinônimos.
    """
    
    def __init__(self, caminho_csv: str):
        self.itens: List[ItemConhecimento] = []
        self.motor_tfidf = MotorTFIDF()
        self._carregar_dados(caminho_csv)
        self._construir_indice()
    
    def _carregar_dados(self, caminho: str):
        """Carrega dados do arquivo CSV."""
        try:
            with open(caminho, 'r', encoding='utf-8') as arquivo_csv:
                leitor = csv.DictReader(arquivo_csv)
                for linha in leitor:
                    self.itens.append(ItemConhecimento(
                        categoria=linha['categoria'],
                        pergunta=linha['pergunta'],
                        resposta=linha['resposta'],
                        fonte=linha['fonte']
                    ))
            logger.info(f"Base de conhecimento carregada: {len(self.itens)} itens")
            print(f"Base de conhecimento carregada: {len(self.itens)} itens do arquivo '{caminho}'")
        except FileNotFoundError:
            logger.warning(f"Arquivo '{caminho}' não encontrado")
            print(f"Arquivo '{caminho}' não encontrado. Base de conhecimento vazia.")
        except Exception as erro:
            logger.error(f"Erro ao carregar dados: {erro}")
            print(f"Erro ao carregar dados: {erro}")
    
    def _construir_indice(self):
        """Constrói índice de busca."""
        if not self.itens:
            return
        
        # Criar documentos combinando pergunta e resposta
        documentos = [
            f"{item.categoria} {item.pergunta} {item.resposta}"
            for item in self.itens
        ]
        
        self.motor_tfidf.construir_indice(documentos)
        logger.info("Índice TF-IDF construído")
    
    def buscar_exato(self, consulta: str) -> List[ResultadoBusca]:
        """Busca por correspondência exata de termos."""
        resultados = []
        tokens_consulta = set(ProcessadorTexto.tokenizar(consulta))
        
        for item in self.itens:
            tokens_item = set(ProcessadorTexto.tokenizar(
                f"{item.pergunta} {item.resposta}"
            ))
            
            # Calcular overlap
            intersecao = tokens_consulta & tokens_item
            if intersecao:
                score = len(intersecao) / len(tokens_consulta) if tokens_consulta else 0
                if score > 0.3:  # Threshold mínimo
                    resultados.append(ResultadoBusca(
                        item=item,
                        score_similaridade=score,
                        metodo_match="exato"
                    ))
        
        return resultados
    
    def buscar_tfidf(self, consulta: str, top_k: int = 5) -> List[ResultadoBusca]:
        """Busca usando TF-IDF."""
        if not self.itens:
            return []
        
        scores = []
        for idx in range(len(self.itens)):
            score = self.motor_tfidf.calcular_similaridade(consulta, idx)
            if score > 0.1:  # Threshold mínimo
                scores.append((idx, score))
        
        # Ordenar por score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        resultados = []
        for idx, score in scores[:top_k]:
            resultados.append(ResultadoBusca(
                item=self.itens[idx],
                score_similaridade=score,
                metodo_match="tfidf"
            ))
        
        return resultados
    
    def buscar_por_categoria(self, categoria: str) -> List[ResultadoBusca]:
        """Busca por categoria específica."""
        resultados = []
        categoria_norm = ProcessadorTexto.normalizar(categoria)
        
        for item in self.itens:
            if ProcessadorTexto.normalizar(item.categoria) == categoria_norm:
                resultados.append(ResultadoBusca(
                    item=item,
                    score_similaridade=1.0,
                    metodo_match="categoria"
                ))
        
        return resultados
    
    def buscar(self, consulta: str, contexto: Dict = None, top_k: int = 5) -> List[ResultadoBusca]:
        """
        Busca híbrida combinando múltiplos métodos.
        
        Args:
            consulta: Texto da consulta do usuário
            contexto: Contexto adicional (categoria, motivo, etc.)
            top_k: Número máximo de resultados
        
        Returns:
            Lista de ResultadoBusca ordenados por relevância
        """
        resultados_finais = {}
        
        # 1. Busca por categoria se disponível
        if contexto and contexto.get('categoria'):
            for resultado in self.buscar_por_categoria(contexto['categoria']):
                key = resultado.item.fonte
                if key not in resultados_finais:
                    resultados_finais[key] = resultado
                    resultados_finais[key].score_similaridade *= 1.2  # Boost categoria
        
        # 2. Busca TF-IDF
        for resultado in self.buscar_tfidf(consulta, top_k * 2):
            key = resultado.item.fonte
            if key in resultados_finais:
                # Combinar scores
                resultados_finais[key].score_similaridade = max(
                    resultados_finais[key].score_similaridade,
                    resultado.score_similaridade
                )
            else:
                resultados_finais[key] = resultado
        
        # 3. Busca exata (fallback)
        for resultado in self.buscar_exato(consulta):
            key = resultado.item.fonte
            if key in resultados_finais:
                resultados_finais[key].score_similaridade += resultado.score_similaridade * 0.5
            else:
                resultados_finais[key] = resultado
        
        # Ordenar e limitar resultados
        resultados = list(resultados_finais.values())
        resultados.sort(key=lambda x: x.score_similaridade, reverse=True)
        
        logger.info(f"Busca retornou {len(resultados[:top_k])} resultados para: {consulta[:50]}...")
        
        return resultados[:top_k]
    
    def obter_contexto_relevante(self, consulta: str, contexto: Dict = None) -> str:
        """
        Retorna contexto formatado para uso com LLM.
        
        Args:
            consulta: Consulta do usuário
            contexto: Contexto adicional
        
        Returns:
            String formatada com políticas relevantes
        """
        resultados = self.buscar(consulta, contexto)
        
        if not resultados:
            return "Nenhuma política específica encontrada na base de conhecimento."
        
        partes = ["POLÍTICAS RELEVANTES ENCONTRADAS:\n"]
        
        for i, resultado in enumerate(resultados, 1):
            item = resultado.item
            partes.append(f"""
--- Política {i} (Relevância: {resultado.score_similaridade:.0%}) ---
Fonte: {item.fonte}
Categoria: {item.categoria}
Pergunta: {item.pergunta}
Resposta: {item.resposta}
""")
        
        return "\n".join(partes)

"""
Sistema de Logging Estruturado para o Agente de Reembolso.
Fornece logging detalhado para auditoria, debug e análise.
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import traceback


class NivelEvento(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"  # Para eventos de auditoria


class TipoEvento(Enum):
    INICIO_PROCESSAMENTO = "INICIO_PROCESSAMENTO"
    FIM_PROCESSAMENTO = "FIM_PROCESSAMENTO"
    BUSCA_BASE_CONHECIMENTO = "BUSCA_BASE_CONHECIMENTO"
    APLICACAO_POLITICA = "APLICACAO_POLITICA"
    DECISAO_AUTOMATICA = "DECISAO_AUTOMATICA"
    ANALISE_LLM = "ANALISE_LLM"
    CALCULO_SCORE = "CALCULO_SCORE"
    ERRO_SISTEMA = "ERRO_SISTEMA"
    ENTRADA_USUARIO = "ENTRADA_USUARIO"
    SAIDA_SISTEMA = "SAIDA_SISTEMA"


@dataclass
class EventoLog:
    """Estrutura de um evento de log."""
    timestamp: str
    nivel: str
    tipo: str
    mensagem: str
    dados: Dict[str, Any]
    sessao_id: str = ""
    duracao_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class LoggerEstruturado:
    """
    Logger estruturado com suporte a múltiplos destinos.
    Ideal para auditoria e análise de decisões.
    """
    
    _instancia = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    def __init__(
        self, 
        nome: str = "agente_reembolso",
        nivel: int = logging.INFO,
        arquivo_log: str = None,
        formato_json: bool = True
    ):
        if hasattr(self, '_inicializado'):
            return
            
        self._inicializado = True
        self.nome = nome
        self.formato_json = formato_json
        self.sessao_id = self._gerar_sessao_id()
        
        # Configurar logger base
        self.logger = logging.getLogger(nome)
        self.logger.setLevel(nivel)
        self.logger.handlers = []  # Limpar handlers existentes
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(nivel)
        
        if formato_json:
            console_formatter = logging.Formatter('%(message)s')
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo (se especificado)
        if arquivo_log:
            self._configurar_arquivo_log(arquivo_log)
        
        # Criar arquivo de auditoria separado
        self._configurar_arquivo_auditoria()
    
    def _gerar_sessao_id(self) -> str:
        """Gera ID único para a sessão."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _configurar_arquivo_log(self, caminho: str):
        """Configura logging para arquivo."""
        try:
            os.makedirs(os.path.dirname(caminho) if os.path.dirname(caminho) else '.', exist_ok=True)
            file_handler = logging.FileHandler(caminho, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Aviso: Não foi possível criar arquivo de log: {e}")
    
    def _configurar_arquivo_auditoria(self):
        """Configura arquivo de auditoria."""
        try:
            os.makedirs('logs', exist_ok=True)
            self.arquivo_auditoria = f"logs/auditoria_{self.sessao_id}.jsonl"
        except Exception:
            self.arquivo_auditoria = None
    
    def _criar_evento(
        self, 
        nivel: NivelEvento, 
        tipo: TipoEvento, 
        mensagem: str, 
        dados: Dict = None,
        duracao_ms: float = 0.0
    ) -> EventoLog:
        """Cria um evento de log estruturado."""
        return EventoLog(
            timestamp=datetime.now().isoformat(),
            nivel=nivel.value,
            tipo=tipo.value,
            mensagem=mensagem,
            dados=dados or {},
            sessao_id=self.sessao_id,
            duracao_ms=duracao_ms
        )
    
    def _registrar_evento(self, evento: EventoLog, nivel_log: int):
        """Registra evento no logger e arquivo de auditoria."""
        if self.formato_json:
            self.logger.log(nivel_log, evento.to_json())
        else:
            self.logger.log(nivel_log, f"[{evento.tipo}] {evento.mensagem}")
        
        # Salvar em arquivo de auditoria
        if self.arquivo_auditoria:
            try:
                with open(self.arquivo_auditoria, 'a', encoding='utf-8') as f:
                    f.write(evento.to_json() + '\n')
            except Exception:
                pass
    
    def debug(self, mensagem: str, tipo: TipoEvento = None, **dados):
        """Log de debug."""
        evento = self._criar_evento(
            NivelEvento.DEBUG,
            tipo or TipoEvento.INICIO_PROCESSAMENTO,
            mensagem,
            dados
        )
        self._registrar_evento(evento, logging.DEBUG)
    
    def info(self, mensagem: str, tipo: TipoEvento = None, **dados):
        """Log de informação."""
        evento = self._criar_evento(
            NivelEvento.INFO,
            tipo or TipoEvento.INICIO_PROCESSAMENTO,
            mensagem,
            dados
        )
        self._registrar_evento(evento, logging.INFO)
    
    def warning(self, mensagem: str, tipo: TipoEvento = None, **dados):
        """Log de aviso."""
        evento = self._criar_evento(
            NivelEvento.WARNING,
            tipo or TipoEvento.ERRO_SISTEMA,
            mensagem,
            dados
        )
        self._registrar_evento(evento, logging.WARNING)
    
    def error(self, mensagem: str, tipo: TipoEvento = None, excecao: Exception = None, **dados):
        """Log de erro."""
        if excecao:
            dados['excecao'] = str(excecao)
            dados['traceback'] = traceback.format_exc()
        
        evento = self._criar_evento(
            NivelEvento.ERROR,
            tipo or TipoEvento.ERRO_SISTEMA,
            mensagem,
            dados
        )
        self._registrar_evento(evento, logging.ERROR)
    
    def audit(self, mensagem: str, tipo: TipoEvento, **dados):
        """Log de auditoria (sempre registrado)."""
        evento = self._criar_evento(
            NivelEvento.AUDIT,
            tipo,
            mensagem,
            dados
        )
        self._registrar_evento(evento, logging.INFO)
    
    # Métodos específicos para o agente de reembolso
    
    def log_inicio_processamento(self, consulta: str, contexto: Dict):
        """Registra início do processamento de uma solicitação."""
        self.audit(
            "Iniciando processamento de solicitação",
            TipoEvento.INICIO_PROCESSAMENTO,
            consulta=consulta[:100],
            categoria=contexto.get('categoria'),
            status=contexto.get('status'),
            motivo=contexto.get('motivo')
        )
    
    def log_busca_base(self, consulta: str, resultados: int, tempo_ms: float):
        """Registra busca na base de conhecimento."""
        self.info(
            f"Busca na base de conhecimento retornou {resultados} resultados",
            TipoEvento.BUSCA_BASE_CONHECIMENTO,
            consulta=consulta[:50],
            resultados=resultados,
            duracao_ms=tempo_ms
        )
    
    def log_aplicacao_politica(self, codigo_politica: str, decisao: str, confianca: str):
        """Registra aplicação de política."""
        self.audit(
            f"Política aplicada: {codigo_politica}",
            TipoEvento.APLICACAO_POLITICA,
            codigo_politica=codigo_politica,
            decisao=decisao,
            confianca=confianca
        )
    
    def log_decisao(self, decisao: str, confianca: str, justificativa: str, fontes: list):
        """Registra decisão final."""
        self.audit(
            f"Decisão: {decisao} (Confiança: {confianca})",
            TipoEvento.DECISAO_AUTOMATICA,
            decisao=decisao,
            confianca=confianca,
            justificativa=justificativa,
            fontes=fontes
        )
    
    def log_analise_llm(self, provedor: str, decisao: str, confianca: float, tokens: int = 0):
        """Registra análise por LLM."""
        self.info(
            f"Análise LLM ({provedor}): {decisao}",
            TipoEvento.ANALISE_LLM,
            provedor=provedor,
            decisao=decisao,
            confianca=confianca,
            tokens_usados=tokens
        )
    
    def log_score(self, score_final: float, scores_parciais: Dict):
        """Registra cálculo de score."""
        self.info(
            f"Score calculado: {score_final:.3f}",
            TipoEvento.CALCULO_SCORE,
            score_final=score_final,
            scores_parciais=scores_parciais
        )
    
    def log_fim_processamento(self, tempo_total_ms: float, sucesso: bool):
        """Registra fim do processamento."""
        self.audit(
            f"Processamento finalizado {'com sucesso' if sucesso else 'com erros'}",
            TipoEvento.FIM_PROCESSAMENTO,
            tempo_total_ms=tempo_total_ms,
            sucesso=sucesso
        )


# Instância global do logger
def obter_logger() -> LoggerEstruturado:
    """Obtém instância singleton do logger estruturado."""
    return LoggerEstruturado()


# Configuração inicial do módulo logging
def configurar_logging(
    nivel: int = logging.INFO,
    arquivo: str = None,
    formato_json: bool = False
):
    """
    Configura o sistema de logging.
    
    Args:
        nivel: Nível mínimo de log (logging.DEBUG, logging.INFO, etc.)
        arquivo: Caminho para arquivo de log (opcional)
        formato_json: Se True, usa formato JSON estruturado
    """
    # Configurar logging básico para módulos externos
    logging.basicConfig(
        level=nivel,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Inicializar logger estruturado
    return LoggerEstruturado(
        nivel=nivel,
        arquivo_log=arquivo,
        formato_json=formato_json
    )

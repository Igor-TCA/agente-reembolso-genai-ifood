"""
Sistema de Tratamento de Erros e Exceções.
Fornece tratamento robusto e recuperação de falhas.
"""
import functools
import traceback
import logging
from typing import Callable, Any, Optional, TypeVar, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TipoErro(Enum):
    """Tipos de erro do sistema."""
    ARQUIVO_NAO_ENCONTRADO = "ARQUIVO_NAO_ENCONTRADO"
    FORMATO_INVALIDO = "FORMATO_INVALIDO"
    CONEXAO_FALHOU = "CONEXAO_FALHOU"
    TIMEOUT = "TIMEOUT"
    VALIDACAO = "VALIDACAO"
    PROCESSAMENTO = "PROCESSAMENTO"
    DESCONHECIDO = "DESCONHECIDO"


class SeveridadeErro(Enum):
    """Severidade do erro."""
    BAIXA = "BAIXA"      # Pode continuar com fallback
    MEDIA = "MEDIA"      # Deve notificar mas pode continuar
    ALTA = "ALTA"        # Deve parar e reportar
    CRITICA = "CRITICA"  # Sistema instável


@dataclass
class ErroSistema:
    """Estrutura padronizada de erro."""
    tipo: TipoErro
    severidade: SeveridadeErro
    mensagem: str
    detalhes: str = ""
    recuperavel: bool = True
    acao_sugerida: str = ""
    
    def __str__(self):
        return f"[{self.tipo.value}] {self.mensagem}"
    
    def to_dict(self) -> Dict:
        return {
            "tipo": self.tipo.value,
            "severidade": self.severidade.value,
            "mensagem": self.mensagem,
            "detalhes": self.detalhes,
            "recuperavel": self.recuperavel,
            "acao_sugerida": self.acao_sugerida
        }


class ExcecaoAgente(Exception):
    """Exceção base do agente de reembolso."""
    
    def __init__(self, erro: ErroSistema):
        self.erro = erro
        super().__init__(str(erro))


class ExcecaoArquivo(ExcecaoAgente):
    """Exceção relacionada a arquivos."""
    pass


class ExcecaoValidacao(ExcecaoAgente):
    """Exceção de validação de dados."""
    pass


class ExcecaoProcessamento(ExcecaoAgente):
    """Exceção durante processamento."""
    pass


class ExcecaoConexao(ExcecaoAgente):
    """Exceção de conexão com serviços externos."""
    pass


class GerenciadorErros:
    """
    Gerenciador central de erros.
    Fornece tratamento padronizado e logging.
    """
    
    _erros_registrados: list = []
    _max_erros: int = 100
    
    @classmethod
    def registrar(cls, erro: ErroSistema, excecao: Exception = None):
        """Registra um erro no sistema."""
        if len(cls._erros_registrados) >= cls._max_erros:
            cls._erros_registrados.pop(0)
        
        registro = {
            "erro": erro.to_dict(),
            "traceback": traceback.format_exc() if excecao else None
        }
        cls._erros_registrados.append(registro)
        
        # Log baseado na severidade
        if erro.severidade == SeveridadeErro.CRITICA:
            logger.critical(f"{erro} - {erro.detalhes}")
        elif erro.severidade == SeveridadeErro.ALTA:
            logger.error(f"{erro} - {erro.detalhes}")
        elif erro.severidade == SeveridadeErro.MEDIA:
            logger.warning(f"{erro} - {erro.detalhes}")
        else:
            logger.info(f"{erro}")
    
    @classmethod
    def obter_ultimos_erros(cls, quantidade: int = 10) -> list:
        """Retorna os últimos erros registrados."""
        return cls._erros_registrados[-quantidade:]
    
    @classmethod
    def limpar(cls):
        """Limpa histórico de erros."""
        cls._erros_registrados = []


def tratar_excecoes(
    valor_padrao: Any = None,
    tipos_excecao: tuple = (Exception,),
    log_erro: bool = True,
    propagar: bool = False
):
    """
    Decorator para tratamento padronizado de exceções.
    
    Args:
        valor_padrao: Valor a retornar em caso de erro
        tipos_excecao: Tipos de exceção a capturar
        log_erro: Se deve registrar o erro
        propagar: Se deve re-lançar a exceção após tratamento
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except tipos_excecao as e:
                erro = ErroSistema(
                    tipo=_classificar_excecao(e),
                    severidade=SeveridadeErro.MEDIA,
                    mensagem=f"Erro em {func.__name__}: {str(e)}",
                    detalhes=traceback.format_exc(),
                    recuperavel=not propagar,
                    acao_sugerida="Verificar logs para mais detalhes"
                )
                
                if log_erro:
                    GerenciadorErros.registrar(erro, e)
                
                if propagar:
                    raise ExcecaoProcessamento(erro) from e
                
                return valor_padrao
        
        return wrapper
    return decorator


def _classificar_excecao(excecao: Exception) -> TipoErro:
    """Classifica uma exceção em um tipo de erro."""
    if isinstance(excecao, FileNotFoundError):
        return TipoErro.ARQUIVO_NAO_ENCONTRADO
    elif isinstance(excecao, (ValueError, TypeError)):
        return TipoErro.VALIDACAO
    elif isinstance(excecao, (ConnectionError, TimeoutError)):
        return TipoErro.CONEXAO_FALHOU
    elif isinstance(excecao, (json.JSONDecodeError if 'json' in dir() else Exception,)):
        return TipoErro.FORMATO_INVALIDO
    else:
        return TipoErro.DESCONHECIDO


import json


class ValidadorContexto:
    """Validador de contexto de entrada."""
    
    CAMPOS_OBRIGATORIOS = ['status', 'motivo']
    CAMPOS_OPCIONAIS = ['categoria', 'detalhes_adicionais']
    
    STATUS_VALIDOS = [
        'AGUARDANDO_CONFIRMACAO',
        'EM_PREPARACAO', 
        'SAIU_PARA_ENTREGA',
        'ENTREGUE',
        'DESCONHECIDO'
    ]
    
    @classmethod
    def validar(cls, contexto: Dict) -> tuple:
        """
        Valida o contexto de entrada.
        
        Returns:
            tuple: (valido: bool, erros: list)
        """
        erros = []
        
        if not isinstance(contexto, dict):
            erros.append("Contexto deve ser um dicionário")
            return False, erros
        
        # Verificar campos obrigatórios
        for campo in cls.CAMPOS_OBRIGATORIOS:
            if campo not in contexto or not contexto[campo]:
                erros.append(f"Campo obrigatório ausente: {campo}")
        
        # Validar status
        if 'status' in contexto:
            status = contexto['status']
            if status not in cls.STATUS_VALIDOS:
                erros.append(f"Status inválido: {status}. Válidos: {cls.STATUS_VALIDOS}")
        
        # Validar detalhes adicionais
        if 'detalhes_adicionais' in contexto:
            detalhes = contexto['detalhes_adicionais']
            if not isinstance(detalhes, dict):
                erros.append("detalhes_adicionais deve ser um dicionário")
            else:
                # Validar valor_pedido se presente
                if 'valor_pedido' in detalhes:
                    try:
                        valor = detalhes['valor_pedido']
                        if valor:
                            float(str(valor).replace(',', '.').replace('R$', ''))
                    except (ValueError, TypeError):
                        erros.append(f"Valor do pedido inválido: {detalhes['valor_pedido']}")
                
                # Validar tempo_espera se presente
                if 'tempo_espera' in detalhes:
                    try:
                        tempo = detalhes['tempo_espera']
                        if tempo:
                            int(tempo)
                    except (ValueError, TypeError):
                        erros.append(f"Tempo de espera inválido: {detalhes['tempo_espera']}")
        
        return len(erros) == 0, erros
    
    @classmethod
    def normalizar(cls, contexto: Dict) -> Dict:
        """
        Normaliza o contexto, preenchendo valores padrão.
        
        Returns:
            Dict: Contexto normalizado
        """
        normalizado = contexto.copy()
        
        # Garantir que campos existem
        if 'categoria' not in normalizado:
            normalizado['categoria'] = 'suporte'
        
        if 'status' not in normalizado:
            normalizado['status'] = 'DESCONHECIDO'
        
        if 'motivo' not in normalizado:
            normalizado['motivo'] = 'OUTRO'
        
        if 'detalhes_adicionais' not in normalizado:
            normalizado['detalhes_adicionais'] = {}
        
        return normalizado


class RecuperadorFalhas:
    """
    Sistema de recuperação de falhas.
    Implementa estratégias de fallback.
    """
    
    @staticmethod
    def com_fallback(
        funcao_principal: Callable,
        funcao_fallback: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa função principal com fallback em caso de falha.
        
        Args:
            funcao_principal: Função a tentar primeiro
            funcao_fallback: Função de fallback
            *args, **kwargs: Argumentos para as funções
        """
        try:
            return funcao_principal(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Função principal falhou, usando fallback: {e}")
            return funcao_fallback(*args, **kwargs)
    
    @staticmethod
    def com_retry(
        funcao: Callable,
        max_tentativas: int = 3,
        delay_segundos: float = 1.0,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa função com retry em caso de falha.
        
        Args:
            funcao: Função a executar
            max_tentativas: Número máximo de tentativas
            delay_segundos: Delay entre tentativas
        """
        import time
        
        ultima_excecao = None
        
        for tentativa in range(max_tentativas):
            try:
                return funcao(*args, **kwargs)
            except Exception as e:
                ultima_excecao = e
                logger.warning(f"Tentativa {tentativa + 1}/{max_tentativas} falhou: {e}")
                
                if tentativa < max_tentativas - 1:
                    time.sleep(delay_segundos)
        
        raise ultima_excecao
    
    @staticmethod
    def criar_resposta_erro(mensagem: str) -> Dict:
        """
        Cria resposta padrão de erro.
        
        Returns:
            Dict com estrutura de resposta de erro
        """
        return {
            "resposta_final": mensagem,
            "confianca": "Baixa",
            "acao": "ESCALAR",
            "fontes": [],
            "erro": True,
            "metodo_decisao": "erro_fallback"
        }


# Decorator de validação
def validar_entrada(func: Callable) -> Callable:
    """Decorator que valida entrada antes de processar."""
    @functools.wraps(func)
    def wrapper(self, consulta: str, contexto: Dict, *args, **kwargs):
        # Validar consulta
        if not consulta or not isinstance(consulta, str):
            erro = ErroSistema(
                tipo=TipoErro.VALIDACAO,
                severidade=SeveridadeErro.MEDIA,
                mensagem="Consulta inválida ou vazia",
                acao_sugerida="Fornecer uma consulta válida"
            )
            GerenciadorErros.registrar(erro)
            # Criar consulta padrão
            consulta = "Solicitação sem descrição"
        
        # Validar e normalizar contexto
        valido, erros = ValidadorContexto.validar(contexto)
        if not valido:
            logger.warning(f"Contexto com problemas: {erros}")
        
        contexto_normalizado = ValidadorContexto.normalizar(contexto)
        
        return func(self, consulta, contexto_normalizado, *args, **kwargs)
    
    return wrapper

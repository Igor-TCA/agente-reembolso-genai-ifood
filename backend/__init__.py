# Backend - Motor de processamento do agente de reembolso
from .motor_politicas import MotorPoliticasExpandido, SistemaScoring, ResultadoPolitica, DecisaoTipo, ConfiancaNivel
from .busca_semantica import BaseConhecimentoSemantica, ResultadoBusca, ItemConhecimento
from .integracao_llm import GerenciadorLLM, RespostaLLM
from .sistema_logging import obter_logger, configurar_logging, TipoEvento
from .tratamento_erros import (
    tratar_excecoes, 
    validar_entrada,
    ValidadorContexto, 
    RecuperadorFalhas, 
    GerenciadorErros,
    ErroSistema,
    TipoErro,
    SeveridadeErro,
    ExcecaoAgente,
    ExcecaoValidacao,
    ExcecaoProcessamento
)

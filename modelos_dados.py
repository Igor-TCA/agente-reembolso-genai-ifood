"""
Módulo de modelos de dados e mapeamentos.
Contém as estruturas de dados e constantes utilizadas no sistema.
"""
from typing import Dict


class MapeamentoCategoria:
    OPCOES = {
        1: "reembolso",
        2: "financeiro",
        3: "entrega",
        4: "fraude",
        5: "suporte"
    }


class MapeamentoStatus:
    OPCOES = {
        1: "AGUARDANDO_CONFIRMACAO",
        2: "EM_PREPARACAO",
        3: "SAIU_PARA_ENTREGA",
        4: "ENTREGUE",
        5: "DESCONHECIDO"
    }


class MapeamentoMotivo:
    REEMBOLSO = {
        1: "ARREPENDIMENTO_CLIENTE",
        2: "CANCELAMENTO_RESTAURANTE",
        3: "ERRO_RESTAURANTE",
        4: "ERRO_APP",
        5: "ATRASO_ENTREGA"
    }
    
    FINANCEIRO = {
        1: "COBRANCA_POS_CANCELAMENTO",
        2: "COBRANCA_DUPLICADA",
        3: "VALOR_INCORRETO",
        4: "ESTORNO_PENDENTE"
    }
    
    ENTREGA = {
        1: "NAO_RECEBIDO",
        2: "INCOMPLETO",
        3: "PEDIDO_ERRADO",
        4: "ERRO_ENTREGADOR"
    }
    
    FRAUDE = {
        1: "COMPRA_NAO_RECONHECIDA",
        2: "MULTIPLAS_COBRANCAS",
        3: "CONTA_COMPROMETIDA"
    }
    
    OUTROS = {
        1: "OUTRO"
    }
    
    @staticmethod
    def obter_por_tipo(tipo_problema: int) -> Dict[int, str]:
        mapeamentos = {
            1: MapeamentoMotivo.REEMBOLSO,
            2: MapeamentoMotivo.FINANCEIRO,
            3: MapeamentoMotivo.ENTREGA,
            4: MapeamentoMotivo.FRAUDE,
            5: MapeamentoMotivo.OUTROS
        }
        return mapeamentos.get(tipo_problema, MapeamentoMotivo.OUTROS)


class OpcoesMenu:
    TIPO_PROBLEMA = [
        "Quero cancelar meu pedido e receber reembolso",
        "Fui cobrado incorretamente",
        "Meu pedido não chegou ou veio errado",
        "Suspeita de fraude ou cobrança duplicada",
        "Outro problema"
    ]
    
    STATUS_PEDIDO = [
        "Pedido ainda não foi confirmado pelo restaurante",
        "Pedido está sendo preparado",
        "Pedido saiu para entrega",
        "Pedido foi entregue",
        "Não sei o status"
    ]
    
    MOTIVO_REEMBOLSO = [
        "Mudei de ideia / Desisti do pedido",
        "Restaurante cancelou ou não tem o item",
        "Erro no pedido (item errado, falta ingrediente)",
        "Problema com o aplicativo",
        "Demora excessiva"
    ]
    
    MOTIVO_FINANCEIRO = [
        "Fui cobrado após cancelamento",
        "Cobrança duplicada",
        "Valor cobrado está errado",
        "Estorno não caiu na conta"
    ]
    
    MOTIVO_ENTREGA = [
        "Pedido não chegou (mas consta como entregue)",
        "Pedido chegou incompleto",
        "Pedido veio errado/trocado",
        "Entregador não encontrou o endereço"
    ]
    
    MOTIVO_FRAUDE = [
        "Não reconheço a compra",
        "Múltiplas cobranças suspeitas",
        "Conta invadida"
    ]
    
    MOTIVO_OUTROS = [
        "Problema não listado acima"
    ]
    
    @staticmethod
    def obter_opcoes_motivo(tipo_problema: int) -> list:
        opcoes = {
            1: OpcoesMenu.MOTIVO_REEMBOLSO,
            2: OpcoesMenu.MOTIVO_FINANCEIRO,
            3: OpcoesMenu.MOTIVO_ENTREGA,
            4: OpcoesMenu.MOTIVO_FRAUDE,
            5: OpcoesMenu.MOTIVO_OUTROS
        }
        return opcoes.get(tipo_problema, OpcoesMenu.MOTIVO_OUTROS)


class TemplatesConsulta:
    TEMPLATES = {
        "ARREPENDIMENTO_CLIENTE": "Quero cancelar, o pedido já saiu mas mudei de ideia",
        "ERRO_RESTAURANTE": "Veio errado, o pedido saiu agora",
        "ERRO_APP": "O aplicativo deu erro e fez pedido duplicado",
        "CANCELAMENTO_RESTAURANTE": "O restaurante cancelou meu pedido",
        "COBRANCA_DUPLICADA": "Fui cobrado duas vezes pelo mesmo pedido",
        "NAO_RECEBIDO": "Meu pedido não chegou mas está marcado como entregue",
        "COMPRA_NAO_RECONHECIDA": "Não fiz esse pedido, suspeito de fraude"
    }
    
    @staticmethod
    def obter_template(motivo: str, categoria: str = "") -> str:
        return TemplatesConsulta.TEMPLATES.get(
            motivo, 
            f"Problema com pedido - categoria: {categoria}, motivo: {motivo}"
        )


def criar_contexto_vazio() -> Dict:
    return {
        "consulta_usuario": "",
        "contexto": {
            "status": "",
            "motivo": "",
            "categoria": "",
            "detalhes_adicionais": {}
        }
    }

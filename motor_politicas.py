"""
Motor de Políticas Expandido para o Sistema de Reembolso iFood.
Contém regras determinísticas abrangentes para tomada de decisão automática.
"""
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DecisaoTipo(Enum):
    APROVAR = "APROVAR"
    REJEITAR = "REJEITAR"
    ESCALAR = "ESCALAR"
    ANALISE_MANUAL = "ANALISE_MANUAL"


class ConfiancaNivel(Enum):
    ALTA = "Alta"
    MEDIA = "Média"
    BAIXA = "Baixa"


@dataclass
class ResultadoPolitica:
    """Resultado da avaliação de políticas."""
    decisao: DecisaoTipo
    confianca: ConfiancaNivel
    codigo_politica: str
    justificativa: str
    pontuacao: float = 0.0
    fatores: Dict = None
    
    def __post_init__(self):
        if self.fatores is None:
            self.fatores = {}


class MotorPoliticasExpandido:
    """
    Motor de regras determinísticas expandido.
    Avalia contexto e aplica políticas de reembolso do iFood.
    """
    
    # Limites de tempo (em minutos)
    TEMPO_LIMITE_CANCELAMENTO_GRATUITO = 5
    TEMPO_ATRASO_SIGNIFICATIVO = 30
    TEMPO_ATRASO_CRITICO = 60
    
    # Limites de valor (em reais)
    VALOR_BAIXO = 30.0
    VALOR_MEDIO = 100.0
    VALOR_ALTO = 300.0
    
    def __init__(self):
        self.regras_executadas = []
    
    def avaliar(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """
        Avalia o contexto e retorna a decisão baseada em políticas.
        Executa regras em ordem de prioridade.
        """
        self.regras_executadas = []
        
        # Lista de regras em ordem de prioridade
        regras = [
            self._regra_fraude_detectada,
            self._regra_conta_comprometida,
            self._regra_cancelamento_restaurante,
            self._regra_erro_app_comprovado,
            self._regra_pedido_nao_confirmado,
            self._regra_erro_restaurante,
            self._regra_erro_entregador,
            self._regra_pedido_nao_recebido,
            self._regra_pedido_incompleto,
            self._regra_cobranca_duplicada,
            self._regra_cobranca_pos_cancelamento,
            self._regra_atraso_excessivo,
            self._regra_arrependimento_antes_preparo,
            self._regra_arrependimento_apos_saida,
            self._regra_valor_alto_analise_manual,
            self._regra_multiplos_reembolsos_suspeito,
        ]
        
        for regra in regras:
            resultado = regra(contexto)
            if resultado:
                self.regras_executadas.append(resultado.codigo_politica)
                logger.info(f"Regra ativada: {resultado.codigo_politica}")
                return resultado
        
        return None
    
    def _extrair_valor(self, contexto: Dict) -> Optional[float]:
        """Extrai o valor do pedido do contexto."""
        try:
            detalhes = contexto.get('detalhes_adicionais', {})
            valor_str = detalhes.get('valor_pedido', '')
            if valor_str:
                return float(valor_str.replace(',', '.').replace('R$', '').strip())
        except (ValueError, TypeError):
            pass
        return None
    
    def _extrair_tempo_espera(self, contexto: Dict) -> Optional[int]:
        """Extrai o tempo de espera do contexto."""
        try:
            detalhes = contexto.get('detalhes_adicionais', {})
            tempo_str = detalhes.get('tempo_espera', '')
            if tempo_str:
                return int(tempo_str)
        except (ValueError, TypeError):
            pass
        return None
    
    # ==================== REGRAS DE FRAUDE ====================
    
    def _regra_fraude_detectada(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA F1: Compra não reconhecida - encaminhar para análise de fraude."""
        if contexto.get('categoria') == 'fraude' and contexto.get('motivo') == 'COMPRA_NAO_RECONHECIDA':
            return ResultadoPolitica(
                decisao=DecisaoTipo.ANALISE_MANUAL,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="FRAUDE_F1",
                justificativa="Compra não reconhecida detectada. Encaminhando para equipe antifraude com bloqueio preventivo.",
                pontuacao=0.95,
                fatores={"categoria": "fraude", "acao_imediata": "bloqueio_preventivo"}
            )
        return None
    
    def _regra_conta_comprometida(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA F2: Conta comprometida - ação imediata de segurança."""
        if contexto.get('categoria') == 'fraude' and contexto.get('motivo') == 'CONTA_COMPROMETIDA':
            return ResultadoPolitica(
                decisao=DecisaoTipo.ANALISE_MANUAL,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="FRAUDE_F2",
                justificativa="Conta possivelmente comprometida. Bloqueio preventivo ativado e encaminhado para equipe de segurança.",
                pontuacao=0.98,
                fatores={"categoria": "fraude", "urgencia": "critica", "acao": "bloqueio_conta"}
            )
        return None
    
    def _regra_multiplos_reembolsos_suspeito(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA F3: Múltiplas cobranças suspeitas."""
        if contexto.get('motivo') == 'MULTIPLAS_COBRANCAS':
            return ResultadoPolitica(
                decisao=DecisaoTipo.ANALISE_MANUAL,
                confianca=ConfiancaNivel.MEDIA,
                codigo_politica="FRAUDE_F3",
                justificativa="Múltiplas cobranças detectadas. Requer análise financeira detalhada.",
                pontuacao=0.75,
                fatores={"categoria": "fraude", "tipo": "multiplas_cobrancas"}
            )
        return None
    
    # ==================== REGRAS DE CANCELAMENTO ====================
    
    def _regra_cancelamento_restaurante(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA C1: Restaurante cancelou o pedido - reembolso automático."""
        if contexto.get('motivo') == 'CANCELAMENTO_RESTAURANTE':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="CANCELAMENTO_C1",
                justificativa="Cancelamento realizado pelo restaurante. Reembolso total automático conforme Política 2.1.",
                pontuacao=1.0,
                fatores={"responsavel": "restaurante", "reembolso": "total"}
            )
        return None
    
    def _regra_erro_app_comprovado(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA C2: Erro do aplicativo - reembolso automático."""
        if contexto.get('motivo') == 'ERRO_APP':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="CANCELAMENTO_C2",
                justificativa="Erro do aplicativo confirmado. Reembolso total automático conforme Política 2.1.",
                pontuacao=1.0,
                fatores={"responsavel": "aplicativo", "reembolso": "total"}
            )
        return None
    
    def _regra_pedido_nao_confirmado(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA C3: Cancelamento antes da confirmação - reembolso imediato."""
        if contexto.get('status') == 'AGUARDANDO_CONFIRMACAO':
            motivo = contexto.get('motivo', '')
            if motivo in ['ARREPENDIMENTO_CLIENTE', 'CANCELAMENTO_RESTAURANTE', 'ERRO_APP']:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.APROVAR,
                    confianca=ConfiancaNivel.ALTA,
                    codigo_politica="CANCELAMENTO_C3",
                    justificativa="Pedido ainda não confirmado pelo restaurante. Cancelamento permitido com reembolso total.",
                    pontuacao=1.0,
                    fatores={"status": "pre_confirmacao", "reembolso": "total"}
                )
        return None
    
    # ==================== REGRAS DE ERRO ====================
    
    def _regra_erro_restaurante(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA E1: Erro do restaurante - reembolso aprovado."""
        if contexto.get('motivo') == 'ERRO_RESTAURANTE':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="ERRO_E1",
                justificativa="Erro do restaurante confirmado. Reembolso total aprovado conforme Política 2.1.",
                pontuacao=0.95,
                fatores={"responsavel": "restaurante", "tipo_erro": "preparo"}
            )
        return None
    
    def _regra_erro_entregador(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA E2: Erro do entregador - reembolso aprovado."""
        if contexto.get('motivo') == 'ERRO_ENTREGADOR':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="ERRO_E2",
                justificativa="Erro do entregador confirmado. Reembolso aprovado conforme Política 2.2.",
                pontuacao=0.90,
                fatores={"responsavel": "entregador", "tipo_erro": "entrega"}
            )
        return None
    
    # ==================== REGRAS DE ENTREGA ====================
    
    def _regra_pedido_nao_recebido(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA D1: Pedido não recebido mas marcado como entregue."""
        if contexto.get('motivo') == 'NAO_RECEBIDO':
            valor = self._extrair_valor(contexto)
            if valor and valor > self.VALOR_ALTO:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.ANALISE_MANUAL,
                    confianca=ConfiancaNivel.MEDIA,
                    codigo_politica="ENTREGA_D1_ALTO_VALOR",
                    justificativa=f"Pedido não recebido com valor alto (R${valor:.2f}). Requer validação manual.",
                    pontuacao=0.70,
                    fatores={"problema": "nao_recebido", "valor": valor, "analise": "manual"}
                )
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.MEDIA,
                codigo_politica="ENTREGA_D1",
                justificativa="Pedido não recebido. Aprovado para reembolso após validação do status.",
                pontuacao=0.80,
                fatores={"problema": "nao_recebido", "validacao": "status_entrega"}
            )
        return None
    
    def _regra_pedido_incompleto(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA D2: Pedido chegou incompleto."""
        if contexto.get('motivo') == 'INCOMPLETO':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.MEDIA,
                codigo_politica="ENTREGA_D2",
                justificativa="Pedido incompleto. Reembolso parcial aprovado para itens faltantes.",
                pontuacao=0.85,
                fatores={"problema": "incompleto", "reembolso": "parcial"}
            )
        return None
    
    # ==================== REGRAS FINANCEIRAS ====================
    
    def _regra_cobranca_duplicada(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA FIN1: Cobrança duplicada detectada."""
        if contexto.get('motivo') == 'COBRANCA_DUPLICADA':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="FINANCEIRO_FIN1",
                justificativa="Cobrança duplicada confirmada. Estorno automático da segunda cobrança.",
                pontuacao=0.95,
                fatores={"tipo": "cobranca_duplicada", "acao": "estorno_automatico"}
            )
        return None
    
    def _regra_cobranca_pos_cancelamento(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA FIN2: Cobrança após cancelamento."""
        if contexto.get('motivo') == 'COBRANCA_POS_CANCELAMENTO':
            return ResultadoPolitica(
                decisao=DecisaoTipo.APROVAR,
                confianca=ConfiancaNivel.ALTA,
                codigo_politica="FINANCEIRO_FIN2",
                justificativa="Cobrança indevida após cancelamento. Estorno aprovado.",
                pontuacao=0.90,
                fatores={"tipo": "cobranca_indevida", "acao": "estorno"}
            )
        return None
    
    # ==================== REGRAS DE ATRASO ====================
    
    def _regra_atraso_excessivo(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA A1: Atraso excessivo na entrega."""
        if contexto.get('motivo') == 'ATRASO_ENTREGA':
            tempo = self._extrair_tempo_espera(contexto)
            
            if tempo and tempo >= self.TEMPO_ATRASO_CRITICO:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.APROVAR,
                    confianca=ConfiancaNivel.ALTA,
                    codigo_politica="ATRASO_A1_CRITICO",
                    justificativa=f"Atraso crítico de {tempo} minutos. Reembolso total aprovado.",
                    pontuacao=0.95,
                    fatores={"tempo_espera": tempo, "nivel": "critico"}
                )
            elif tempo and tempo >= self.TEMPO_ATRASO_SIGNIFICATIVO:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.APROVAR,
                    confianca=ConfiancaNivel.MEDIA,
                    codigo_politica="ATRASO_A1_SIGNIFICATIVO",
                    justificativa=f"Atraso significativo de {tempo} minutos. Compensação aprovada.",
                    pontuacao=0.80,
                    fatores={"tempo_espera": tempo, "nivel": "significativo", "reembolso": "parcial"}
                )
            else:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.ESCALAR,
                    confianca=ConfiancaNivel.BAIXA,
                    codigo_politica="ATRASO_A1_MODERADO",
                    justificativa="Atraso reportado. Requer análise do tempo estimado vs real.",
                    pontuacao=0.50,
                    fatores={"tempo_espera": tempo, "nivel": "moderado"}
                )
        return None
    
    # ==================== REGRAS DE ARREPENDIMENTO ====================
    
    def _regra_arrependimento_antes_preparo(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA R1: Arrependimento antes do preparo - permitido."""
        if contexto.get('motivo') == 'ARREPENDIMENTO_CLIENTE':
            if contexto.get('status') in ['AGUARDANDO_CONFIRMACAO', 'EM_PREPARACAO']:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.APROVAR,
                    confianca=ConfiancaNivel.ALTA,
                    codigo_politica="ARREPENDIMENTO_R1",
                    justificativa="Cancelamento por arrependimento antes da saída para entrega. Reembolso aprovado.",
                    pontuacao=0.90,
                    fatores={"motivo": "arrependimento", "fase": "pre_entrega"}
                )
        return None
    
    def _regra_arrependimento_apos_saida(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA R2: Arrependimento após saída para entrega - não elegível."""
        if contexto.get('motivo') == 'ARREPENDIMENTO_CLIENTE':
            if contexto.get('status') in ['SAIU_PARA_ENTREGA', 'ENTREGUE']:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.REJEITAR,
                    confianca=ConfiancaNivel.ALTA,
                    codigo_politica="ARREPENDIMENTO_R2",
                    justificativa="Desistência após saída para entrega não é elegível para reembolso conforme Política 4.1.",
                    pontuacao=0.95,
                    fatores={"motivo": "arrependimento", "fase": "pos_saida", "elegivel": False}
                )
        return None
    
    # ==================== REGRAS DE VALOR ====================
    
    def _regra_valor_alto_analise_manual(self, contexto: Dict) -> Optional[ResultadoPolitica]:
        """POLÍTICA V1: Pedidos de alto valor requerem análise manual."""
        valor = self._extrair_valor(contexto)
        if valor and valor > self.VALOR_ALTO:
            # Apenas se não houver regra mais específica já aplicada
            if contexto.get('categoria') not in ['fraude']:
                return ResultadoPolitica(
                    decisao=DecisaoTipo.ANALISE_MANUAL,
                    confianca=ConfiancaNivel.MEDIA,
                    codigo_politica="VALOR_V1",
                    justificativa=f"Pedido de alto valor (R${valor:.2f}) requer análise manual adicional.",
                    pontuacao=0.60,
                    fatores={"valor": valor, "motivo": "alto_valor"}
                )
        return None


class SistemaScoring:
    """
    Sistema de pontuação para decisões de reembolso.
    Calcula score baseado em múltiplos fatores.
    """
    
    # Pesos dos fatores
    PESOS = {
        "historico_cliente": 0.15,
        "valor_pedido": 0.20,
        "tipo_problema": 0.25,
        "tempo_resposta": 0.10,
        "evidencias": 0.20,
        "politica_aplicavel": 0.10
    }
    
    @staticmethod
    def calcular_score(contexto: Dict, resultado_politica: Optional[ResultadoPolitica] = None) -> Dict:
        """
        Calcula score de reembolso baseado em múltiplos fatores.
        Retorna dict com score total e breakdown.
        """
        scores = {}
        
        # 1. Score baseado no tipo de problema
        scores["tipo_problema"] = SistemaScoring._score_tipo_problema(contexto)
        
        # 2. Score baseado no valor
        scores["valor_pedido"] = SistemaScoring._score_valor(contexto)
        
        # 3. Score baseado no status
        scores["status_pedido"] = SistemaScoring._score_status(contexto)
        
        # 4. Score baseado no motivo
        scores["motivo"] = SistemaScoring._score_motivo(contexto)
        
        # 5. Score da política aplicada
        if resultado_politica:
            scores["politica"] = resultado_politica.pontuacao
        else:
            scores["politica"] = 0.5
        
        # Calcular score final ponderado
        score_final = (
            scores["tipo_problema"] * 0.25 +
            scores["valor_pedido"] * 0.15 +
            scores["status_pedido"] * 0.15 +
            scores["motivo"] * 0.25 +
            scores["politica"] * 0.20
        )
        
        return {
            "score_final": round(score_final, 3),
            "scores_parciais": scores,
            "recomendacao": SistemaScoring._gerar_recomendacao(score_final)
        }
    
    @staticmethod
    def _score_tipo_problema(contexto: Dict) -> float:
        """Pontuação baseada na categoria do problema."""
        scores_categoria = {
            "fraude": 0.9,  # Alta prioridade
            "entrega": 0.8,
            "reembolso": 0.7,
            "financeiro": 0.75,
            "suporte": 0.5
        }
        return scores_categoria.get(contexto.get("categoria", ""), 0.5)
    
    @staticmethod
    def _score_valor(contexto: Dict) -> float:
        """Pontuação baseada no valor do pedido."""
        try:
            detalhes = contexto.get('detalhes_adicionais', {})
            valor_str = detalhes.get('valor_pedido', '')
            if valor_str:
                valor = float(valor_str.replace(',', '.').replace('R$', '').strip())
                if valor <= 30:
                    return 0.9  # Baixo risco
                elif valor <= 100:
                    return 0.7
                elif valor <= 300:
                    return 0.5
                else:
                    return 0.3  # Alto valor = mais cautela
        except (ValueError, TypeError):
            pass
        return 0.5
    
    @staticmethod
    def _score_status(contexto: Dict) -> float:
        """Pontuação baseada no status do pedido."""
        scores_status = {
            "AGUARDANDO_CONFIRMACAO": 0.95,  # Fácil cancelar
            "EM_PREPARACAO": 0.7,
            "SAIU_PARA_ENTREGA": 0.4,
            "ENTREGUE": 0.3,
            "DESCONHECIDO": 0.5
        }
        return scores_status.get(contexto.get("status", ""), 0.5)
    
    @staticmethod
    def _score_motivo(contexto: Dict) -> float:
        """Pontuação baseada no motivo do problema."""
        scores_motivo = {
            # Alta elegibilidade
            "CANCELAMENTO_RESTAURANTE": 1.0,
            "ERRO_RESTAURANTE": 0.95,
            "ERRO_APP": 0.95,
            "ERRO_ENTREGADOR": 0.9,
            "NAO_RECEBIDO": 0.85,
            "COBRANCA_DUPLICADA": 0.9,
            "COBRANCA_POS_CANCELAMENTO": 0.9,
            # Média elegibilidade
            "INCOMPLETO": 0.75,
            "PEDIDO_ERRADO": 0.75,
            "ATRASO_ENTREGA": 0.6,
            "VALOR_INCORRETO": 0.7,
            # Baixa elegibilidade
            "ARREPENDIMENTO_CLIENTE": 0.3,
            # Casos especiais
            "COMPRA_NAO_RECONHECIDA": 0.8,
            "CONTA_COMPROMETIDA": 0.85,
            "MULTIPLAS_COBRANCAS": 0.7
        }
        return scores_motivo.get(contexto.get("motivo", ""), 0.5)
    
    @staticmethod
    def _gerar_recomendacao(score: float) -> str:
        """Gera recomendação baseada no score."""
        if score >= 0.8:
            return "APROVAR - Alta confiança na elegibilidade"
        elif score >= 0.6:
            return "APROVAR_COM_ANALISE - Requer validação adicional"
        elif score >= 0.4:
            return "ESCALAR - Caso requer análise humana"
        else:
            return "REJEITAR - Baixa elegibilidade para reembolso"

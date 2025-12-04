"""
Módulo de Integração com LLMs (Large Language Models).
Suporta OpenAI GPT e Google Gemini para análise contextual.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ProvedorLLM(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"  # Fallback sem API


@dataclass
class RespostaLLM:
    """Resposta do modelo LLM."""
    texto: str
    decisao_sugerida: str
    confianca: float
    justificativa: str
    tokens_usados: int = 0
    modelo: str = ""
    sucesso: bool = True
    erro: str = ""


class InterfaceLLM(ABC):
    """Interface abstrata para provedores de LLM."""
    
    @abstractmethod
    def analisar(self, prompt: str, contexto: Dict) -> RespostaLLM:
        """Analisa a solicitação usando o LLM."""
        pass
    
    @abstractmethod
    def esta_disponivel(self) -> bool:
        """Verifica se o provedor está disponível."""
        pass


class ClienteOpenAI(InterfaceLLM):
    """Cliente para API OpenAI."""
    
    def __init__(self, api_key: str = None, modelo: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.modelo = modelo
        self._cliente = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self._cliente = OpenAI(api_key=self.api_key)
                logger.info(f"Cliente OpenAI inicializado com modelo {modelo}")
            except ImportError:
                logger.warning("Biblioteca openai não instalada. Use: pip install openai")
            except Exception as e:
                logger.error(f"Erro ao inicializar OpenAI: {e}")
    
    def esta_disponivel(self) -> bool:
        return self._cliente is not None
    
    def analisar(self, prompt: str, contexto: Dict) -> RespostaLLM:
        if not self.esta_disponivel():
            return RespostaLLM(
                texto="",
                decisao_sugerida="ESCALAR",
                confianca=0.0,
                justificativa="API OpenAI não disponível",
                sucesso=False,
                erro="Cliente não inicializado"
            )
        
        try:
            system_prompt = self._criar_system_prompt()
            user_prompt = self._criar_user_prompt(prompt, contexto)
            
            response = self._cliente.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            resposta_texto = response.choices[0].message.content
            tokens_usados = response.usage.total_tokens if response.usage else 0
            
            # Parsear resposta estruturada
            resultado = self._parsear_resposta(resposta_texto)
            resultado.tokens_usados = tokens_usados
            resultado.modelo = self.modelo
            
            logger.info(f"OpenAI análise concluída. Decisão: {resultado.decisao_sugerida}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na chamada OpenAI: {e}")
            return RespostaLLM(
                texto="",
                decisao_sugerida="ESCALAR",
                confianca=0.0,
                justificativa=f"Erro na API: {str(e)}",
                sucesso=False,
                erro=str(e)
            )
    
    def _criar_system_prompt(self) -> str:
        return """Você é um agente especializado em análise de solicitações de reembolso do iFood.
Seu papel é analisar cada caso e fornecer uma recomendação baseada nas políticas da empresa.

POLÍTICAS PRINCIPAIS:
1. Cancelamentos antes da confirmação do restaurante: REEMBOLSO TOTAL
2. Erros do restaurante ou app: REEMBOLSO TOTAL
3. Arrependimento após saída para entrega: NÃO ELEGÍVEL
4. Pedido não recebido: REEMBOLSO após validação
5. Fraude suspeita: ANÁLISE MANUAL obrigatória

Responda SEMPRE no formato JSON:
{
    "decisao": "APROVAR|REJEITAR|ESCALAR",
    "confianca": 0.0-1.0,
    "justificativa": "Explicação clara da decisão"
}"""
    
    def _criar_user_prompt(self, prompt: str, contexto: Dict) -> str:
        return f"""Analise a seguinte solicitação de reembolso:

RECLAMAÇÃO DO CLIENTE:
{prompt}

CONTEXTO DO PEDIDO:
- Categoria: {contexto.get('categoria', 'N/A')}
- Status do Pedido: {contexto.get('status', 'N/A')}
- Motivo: {contexto.get('motivo', 'N/A')}
- Detalhes Adicionais: {json.dumps(contexto.get('detalhes_adicionais', {}), ensure_ascii=False)}

POLÍTICAS RELEVANTES:
{contexto.get('politicas_relevantes', 'Nenhuma política específica encontrada.')}

Forneça sua análise em formato JSON."""
    
    def _parsear_resposta(self, texto: str) -> RespostaLLM:
        try:
            # Tentar extrair JSON da resposta
            inicio = texto.find('{')
            fim = texto.rfind('}') + 1
            if inicio != -1 and fim > inicio:
                json_str = texto[inicio:fim]
                dados = json.loads(json_str)
                
                return RespostaLLM(
                    texto=texto,
                    decisao_sugerida=dados.get('decisao', 'ESCALAR'),
                    confianca=float(dados.get('confianca', 0.5)),
                    justificativa=dados.get('justificativa', 'Sem justificativa'),
                    sucesso=True
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Erro ao parsear resposta JSON: {e}")
        
        # Fallback: análise heurística
        decisao = "ESCALAR"
        if "aprovar" in texto.lower() or "reembolso" in texto.lower():
            decisao = "APROVAR"
        elif "rejeitar" in texto.lower() or "não elegível" in texto.lower():
            decisao = "REJEITAR"
        
        return RespostaLLM(
            texto=texto,
            decisao_sugerida=decisao,
            confianca=0.5,
            justificativa=texto[:200],
            sucesso=True
        )


class ClienteGemini(InterfaceLLM):
    """Cliente para API Google Gemini."""
    
    def __init__(self, api_key: str = None, modelo: str = "gemini-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.modelo = modelo
        self._cliente = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._cliente = genai.GenerativeModel(modelo)
                logger.info(f"Cliente Gemini inicializado com modelo {modelo}")
            except ImportError:
                logger.warning("Biblioteca google-generativeai não instalada. Use: pip install google-generativeai")
            except Exception as e:
                logger.error(f"Erro ao inicializar Gemini: {e}")
    
    def esta_disponivel(self) -> bool:
        return self._cliente is not None
    
    def analisar(self, prompt: str, contexto: Dict) -> RespostaLLM:
        if not self.esta_disponivel():
            return RespostaLLM(
                texto="",
                decisao_sugerida="ESCALAR",
                confianca=0.0,
                justificativa="API Gemini não disponível",
                sucesso=False,
                erro="Cliente não inicializado"
            )
        
        try:
            prompt_completo = self._criar_prompt_completo(prompt, contexto)
            
            response = self._cliente.generate_content(prompt_completo)
            resposta_texto = response.text
            
            resultado = self._parsear_resposta(resposta_texto)
            resultado.modelo = self.modelo
            
            logger.info(f"Gemini análise concluída. Decisão: {resultado.decisao_sugerida}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na chamada Gemini: {e}")
            return RespostaLLM(
                texto="",
                decisao_sugerida="ESCALAR",
                confianca=0.0,
                justificativa=f"Erro na API: {str(e)}",
                sucesso=False,
                erro=str(e)
            )
    
    def _criar_prompt_completo(self, prompt: str, contexto: Dict) -> str:
        return f"""Você é um agente especializado em análise de solicitações de reembolso do iFood.

POLÍTICAS PRINCIPAIS:
1. Cancelamentos antes da confirmação: REEMBOLSO TOTAL
2. Erros do restaurante ou app: REEMBOLSO TOTAL  
3. Arrependimento após saída para entrega: NÃO ELEGÍVEL
4. Pedido não recebido: REEMBOLSO após validação
5. Fraude suspeita: ANÁLISE MANUAL obrigatória

RECLAMAÇÃO DO CLIENTE:
{prompt}

CONTEXTO DO PEDIDO:
- Categoria: {contexto.get('categoria', 'N/A')}
- Status: {contexto.get('status', 'N/A')}
- Motivo: {contexto.get('motivo', 'N/A')}
- Detalhes: {json.dumps(contexto.get('detalhes_adicionais', {}), ensure_ascii=False)}

POLÍTICAS RELEVANTES:
{contexto.get('politicas_relevantes', 'Nenhuma política específica encontrada.')}

Responda em JSON:
{{"decisao": "APROVAR|REJEITAR|ESCALAR", "confianca": 0.0-1.0, "justificativa": "..."}}"""
    
    def _parsear_resposta(self, texto: str) -> RespostaLLM:
        try:
            inicio = texto.find('{')
            fim = texto.rfind('}') + 1
            if inicio != -1 and fim > inicio:
                json_str = texto[inicio:fim]
                dados = json.loads(json_str)
                
                return RespostaLLM(
                    texto=texto,
                    decisao_sugerida=dados.get('decisao', 'ESCALAR'),
                    confianca=float(dados.get('confianca', 0.5)),
                    justificativa=dados.get('justificativa', 'Sem justificativa'),
                    sucesso=True
                )
        except (json.JSONDecodeError, ValueError):
            pass
        
        decisao = "ESCALAR"
        if "aprovar" in texto.lower():
            decisao = "APROVAR"
        elif "rejeitar" in texto.lower():
            decisao = "REJEITAR"
        
        return RespostaLLM(
            texto=texto,
            decisao_sugerida=decisao,
            confianca=0.5,
            justificativa=texto[:200],
            sucesso=True
        )


class AnalisadorLocalAvancado(InterfaceLLM):
    """
    Analisador local avançado sem dependência de API externa.
    Usa heurísticas sofisticadas para análise.
    """
    
    def __init__(self):
        self.palavras_positivas = {
            'erro', 'errado', 'incorreto', 'problema', 'falha', 'defeito',
            'cancelou', 'cancelado', 'não chegou', 'não recebi', 'faltando',
            'duplicado', 'duplicada', 'fraude', 'invadido', 'hackeado',
            'cobrança indevida', 'cobrado errado', 'atrasado', 'demora'
        }
        
        self.palavras_negativas = {
            'mudei de ideia', 'desisti', 'não quero mais', 'arrependimento',
            'já comi', 'já recebi', 'entreguei errado o endereço'
        }
        
        logger.info("Analisador local avançado inicializado")
    
    def esta_disponivel(self) -> bool:
        return True
    
    def analisar(self, prompt: str, contexto: Dict) -> RespostaLLM:
        texto_lower = prompt.lower()
        
        # Contagem de indicadores
        score_positivo = sum(1 for p in self.palavras_positivas if p in texto_lower)
        score_negativo = sum(1 for p in self.palavras_negativas if p in texto_lower)
        
        # Analisar contexto
        status = contexto.get('status', '')
        motivo = contexto.get('motivo', '')
        categoria = contexto.get('categoria', '')
        
        # Regras baseadas em contexto
        if categoria == 'fraude':
            return RespostaLLM(
                texto="Análise local: Caso de fraude identificado",
                decisao_sugerida="ESCALAR",
                confianca=0.9,
                justificativa="Casos de fraude requerem análise manual especializada.",
                modelo="local_avancado",
                sucesso=True
            )
        
        if motivo in ['ERRO_RESTAURANTE', 'ERRO_APP', 'CANCELAMENTO_RESTAURANTE']:
            return RespostaLLM(
                texto="Análise local: Erro operacional identificado",
                decisao_sugerida="APROVAR",
                confianca=0.85,
                justificativa=f"Erro operacional ({motivo}) detectado. Elegível para reembolso.",
                modelo="local_avancado",
                sucesso=True
            )
        
        if motivo == 'ARREPENDIMENTO_CLIENTE' and status in ['SAIU_PARA_ENTREGA', 'ENTREGUE']:
            return RespostaLLM(
                texto="Análise local: Arrependimento após entrega",
                decisao_sugerida="REJEITAR",
                confianca=0.9,
                justificativa="Arrependimento após saída para entrega não é elegível.",
                modelo="local_avancado",
                sucesso=True
            )
        
        # Score baseado em palavras-chave
        score_final = (score_positivo - score_negativo) / max(1, score_positivo + score_negativo)
        
        if score_final > 0.3:
            decisao = "APROVAR"
            confianca = 0.6 + (score_final * 0.2)
            justificativa = f"Análise indica elegibilidade. Score: {score_final:.2f}"
        elif score_final < -0.3:
            decisao = "REJEITAR"
            confianca = 0.6 + (abs(score_final) * 0.2)
            justificativa = f"Análise indica não elegibilidade. Score: {score_final:.2f}"
        else:
            decisao = "ESCALAR"
            confianca = 0.5
            justificativa = "Caso requer análise humana para decisão."
        
        return RespostaLLM(
            texto=f"Análise local concluída. Indicadores positivos: {score_positivo}, negativos: {score_negativo}",
            decisao_sugerida=decisao,
            confianca=min(confianca, 0.85),  # Limitar confiança do analisador local
            justificativa=justificativa,
            modelo="local_avancado",
            sucesso=True
        )


class GerenciadorLLM:
    """
    Gerenciador de LLMs com fallback automático.
    Tenta usar o melhor provedor disponível.
    """
    
    def __init__(self):
        self.provedores: Dict[ProvedorLLM, InterfaceLLM] = {}
        self._inicializar_provedores()
    
    def _inicializar_provedores(self):
        """Inicializa todos os provedores disponíveis."""
        # Tentar OpenAI
        openai_client = ClienteOpenAI()
        if openai_client.esta_disponivel():
            self.provedores[ProvedorLLM.OPENAI] = openai_client
            logger.info("OpenAI disponível")
        
        # Tentar Gemini
        gemini_client = ClienteGemini()
        if gemini_client.esta_disponivel():
            self.provedores[ProvedorLLM.GEMINI] = gemini_client
            logger.info("Gemini disponível")
        
        # Sempre disponível: analisador local
        self.provedores[ProvedorLLM.LOCAL] = AnalisadorLocalAvancado()
        logger.info("Analisador local disponível")
    
    def obter_provedor_ativo(self) -> Optional[InterfaceLLM]:
        """Retorna o melhor provedor disponível."""
        ordem_preferencia = [ProvedorLLM.OPENAI, ProvedorLLM.GEMINI, ProvedorLLM.LOCAL]
        
        for provedor in ordem_preferencia:
            if provedor in self.provedores and self.provedores[provedor].esta_disponivel():
                return self.provedores[provedor]
        
        return self.provedores.get(ProvedorLLM.LOCAL)
    
    def analisar(self, prompt: str, contexto: Dict, provedor: ProvedorLLM = None) -> RespostaLLM:
        """
        Analisa usando o provedor especificado ou o melhor disponível.
        
        Args:
            prompt: Consulta do usuário
            contexto: Contexto do pedido
            provedor: Provedor específico (opcional)
        
        Returns:
            RespostaLLM com a análise
        """
        if provedor and provedor in self.provedores:
            cliente = self.provedores[provedor]
        else:
            cliente = self.obter_provedor_ativo()
        
        if not cliente:
            logger.error("Nenhum provedor LLM disponível")
            return RespostaLLM(
                texto="",
                decisao_sugerida="ESCALAR",
                confianca=0.0,
                justificativa="Nenhum provedor de análise disponível",
                sucesso=False,
                erro="Sem provedores"
            )
        
        return cliente.analisar(prompt, contexto)
    
    def listar_provedores_disponiveis(self) -> List[str]:
        """Lista provedores disponíveis."""
        return [
            p.value for p, cliente in self.provedores.items()
            if cliente.esta_disponivel()
        ]

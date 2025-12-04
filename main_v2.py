"""
Sistema de Análise de Reembolso iFood - Versão 2.0
Agente inteligente com busca semântica, motor de políticas expandido e integração LLM.
"""
import json
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Importar módulos do sistema
from motor_politicas import (
    MotorPoliticasExpandido, 
    SistemaScoring, 
    ResultadoPolitica,
    DecisaoTipo,
    ConfiancaNivel
)
from busca_semantica import (
    BaseConhecimentoSemantica, 
    ResultadoBusca,
    ItemConhecimento
)
from integracao_llm import GerenciadorLLM, RespostaLLM
from sistema_logging import (
    obter_logger, 
    configurar_logging,
    TipoEvento
)
from tratamento_erros import (
    tratar_excecoes,
    validar_entrada,
    ValidadorContexto,
    GerenciadorErros,
    RecuperadorFalhas,
    ErroSistema,
    TipoErro,
    SeveridadeErro
)


@dataclass
class RespostaAgente:
    """Resposta completa do agente de reembolso."""
    resposta_final: str
    confianca: str
    acao: str
    fontes: List[str] = field(default_factory=list)
    codigo_politica: str = ""
    score: float = 0.0
    detalhes_score: Dict = field(default_factory=dict)
    tempo_processamento_ms: float = 0.0
    metodo_decisao: str = ""  # "politica", "llm", "fallback"
    
    def to_dict(self) -> Dict:
        return {
            "resposta_final": self.resposta_final,
            "confianca": self.confianca,
            "acao": self.acao,
            "fontes": self.fontes,
            "codigo_politica": self.codigo_politica,
            "score": self.score,
            "detalhes_score": self.detalhes_score,
            "tempo_processamento_ms": self.tempo_processamento_ms,
            "metodo_decisao": self.metodo_decisao
        }


class AgenteReembolsoV2:
    """
    Agente de Reembolso versão 2.0.
    
    Melhorias:
    - Busca semântica com TF-IDF e expansão de sinônimos
    - Motor de políticas expandido (+15 regras)
    - Sistema de scoring transparente
    - Integração com LLMs (OpenAI/Gemini) com fallback local
    - Logging estruturado para auditoria
    - Utilização completa do contexto
    """
    
    def __init__(self, caminho_base: str = "base_conhecimento_ifood_genai-exemplo.csv"):
        self.logger = obter_logger()
        
        # Inicializar componentes
        self.logger.info("Inicializando Agente de Reembolso v2.0", TipoEvento.INICIO_PROCESSAMENTO)
        
        self.base_conhecimento = BaseConhecimentoSemantica(caminho_base)
        self.motor_politicas = MotorPoliticasExpandido()
        self.sistema_scoring = SistemaScoring()
        self.gerenciador_llm = GerenciadorLLM()
        
        # Status dos componentes
        provedores_llm = self.gerenciador_llm.listar_provedores_disponiveis()
        self.logger.info(
            f"Componentes inicializados. LLMs disponíveis: {provedores_llm}",
            TipoEvento.INICIO_PROCESSAMENTO
        )
    
    @tratar_excecoes(valor_padrao=None, log_erro=True)
    def processar_solicitacao(self, consulta_usuario: str, contexto: Dict) -> RespostaAgente:
        """
        Processa solicitação de reembolso com análise completa.
        
        Pipeline:
        1. Busca semântica na base de conhecimento
        2. Aplicação de regras determinísticas
        3. Cálculo de score
        4. Análise LLM (se necessário)
        5. Decisão final
        """
        inicio = time.time()
        self.logger.log_inicio_processamento(consulta_usuario, contexto)
        
        print(f"\n{'='*60}")
        print(f"  PROCESSANDO SOLICITACAO")
        print(f"{'='*60}\n")
        print(f"[>] Consulta: {consulta_usuario[:80]}...")
        
        # ETAPA 1: Busca Semântica
        print("\n[1/5] Realizando busca semântica...")
        tempo_busca = time.time()
        resultados_busca = self.base_conhecimento.buscar(consulta_usuario, contexto)
        tempo_busca_ms = (time.time() - tempo_busca) * 1000
        
        fontes_consultadas = list(set(r.item.fonte for r in resultados_busca))
        
        self.logger.log_busca_base(consulta_usuario, len(resultados_busca), tempo_busca_ms)
        print(f"    [OK] {len(resultados_busca)} politicas encontradas ({tempo_busca_ms:.1f}ms)")
        
        for r in resultados_busca[:3]:
            print(f"      - {r.item.fonte} (similaridade: {r.score_similaridade:.0%})")
        
        # ETAPA 2: Motor de Políticas
        print("\n[2/5] Aplicando regras determinísticas...")
        resultado_politica = self.motor_politicas.avaliar(contexto)
        
        if resultado_politica:
            self.logger.log_aplicacao_politica(
                resultado_politica.codigo_politica,
                resultado_politica.decisao.value,
                resultado_politica.confianca.value
            )
            print(f"    [OK] Regra ativada: {resultado_politica.codigo_politica}")
            print(f"      Decisao: {resultado_politica.decisao.value}")
        else:
            print("    [-] Nenhuma regra deterministica aplicavel")
        
        # ETAPA 3: Cálculo de Score
        print("\n[3/5] Calculando score de elegibilidade...")
        resultado_score = self.sistema_scoring.calcular_score(contexto, resultado_politica)
        
        self.logger.log_score(resultado_score['score_final'], resultado_score['scores_parciais'])
        print(f"    [OK] Score final: {resultado_score['score_final']:.3f}")
        print(f"      Recomendacao: {resultado_score['recomendacao']}")
        
        # ETAPA 4: Decisão
        print("\n[4/5] Tomando decisão...")
        
        # Se há regra determinística com alta confiança, usar diretamente
        if resultado_politica and resultado_politica.confianca == ConfiancaNivel.ALTA:
            resposta = self._criar_resposta_politica(
                resultado_politica, 
                fontes_consultadas, 
                resultado_score
            )
            print(f"    [OK] Decisao por politica deterministica")
        
        # Se nao ha regra ou confianca e baixa, usar LLM
        elif not resultado_politica or resultado_politica.confianca == ConfiancaNivel.BAIXA:
            print("    [>] Acionando analise por IA...")
            
            # Preparar contexto para LLM
            contexto_llm = contexto.copy()
            contexto_llm['politicas_relevantes'] = self.base_conhecimento.obter_contexto_relevante(
                consulta_usuario, contexto
            )
            
            resposta_llm = self.gerenciador_llm.analisar(consulta_usuario, contexto_llm)
            
            self.logger.log_analise_llm(
                resposta_llm.modelo,
                resposta_llm.decisao_sugerida,
                resposta_llm.confianca,
                resposta_llm.tokens_usados
            )
            
            resposta = self._criar_resposta_llm(
                resposta_llm,
                fontes_consultadas,
                resultado_score,
                resultado_politica
            )
            print(f"    [OK] Decisao por analise IA ({resposta_llm.modelo})")
        
        # Confiança média - combinar política com score
        else:
            resposta = self._criar_resposta_combinada(
                resultado_politica,
                fontes_consultadas,
                resultado_score
            )
            print(f"    [OK] Decisao combinada (politica + score)")
        
        # ETAPA 5: Finalização
        tempo_total_ms = (time.time() - inicio) * 1000
        resposta.tempo_processamento_ms = tempo_total_ms
        
        print(f"\n[5/5] Processamento concluído em {tempo_total_ms:.1f}ms")
        
        self.logger.log_decisao(
            resposta.acao,
            resposta.confianca,
            resposta.resposta_final[:100],
            resposta.fontes
        )
        self.logger.log_fim_processamento(tempo_total_ms, True)
        
        return resposta
    
    def _criar_resposta_politica(
        self, 
        politica: ResultadoPolitica,
        fontes: List[str],
        score: Dict
    ) -> RespostaAgente:
        """Cria resposta baseada em política determinística."""
        return RespostaAgente(
            resposta_final=politica.justificativa,
            confianca=politica.confianca.value,
            acao=politica.decisao.value,
            fontes=fontes,
            codigo_politica=politica.codigo_politica,
            score=score['score_final'],
            detalhes_score=score['scores_parciais'],
            metodo_decisao="politica"
        )
    
    def _criar_resposta_llm(
        self,
        resposta_llm: RespostaLLM,
        fontes: List[str],
        score: Dict,
        politica: Optional[ResultadoPolitica] = None
    ) -> RespostaAgente:
        """Cria resposta baseada em análise LLM."""
        # Determinar confiança combinada
        if resposta_llm.confianca >= 0.8:
            confianca = "Alta"
        elif resposta_llm.confianca >= 0.5:
            confianca = "Média"
        else:
            confianca = "Baixa"
        
        codigo = politica.codigo_politica if politica else "LLM_ANALYSIS"
        
        return RespostaAgente(
            resposta_final=resposta_llm.justificativa,
            confianca=confianca,
            acao=resposta_llm.decisao_sugerida,
            fontes=fontes,
            codigo_politica=codigo,
            score=score['score_final'],
            detalhes_score=score['scores_parciais'],
            metodo_decisao=f"llm_{resposta_llm.modelo}"
        )
    
    def _criar_resposta_combinada(
        self,
        politica: ResultadoPolitica,
        fontes: List[str],
        score: Dict
    ) -> RespostaAgente:
        """Cria resposta combinando política e score."""
        # Usar score para ajustar decisão
        if score['score_final'] >= 0.7 and politica.decisao in [DecisaoTipo.APROVAR, DecisaoTipo.ESCALAR]:
            acao = "APROVAR"
            justificativa = f"{politica.justificativa} Score de elegibilidade: {score['score_final']:.0%}"
        elif score['score_final'] < 0.4:
            acao = "REJEITAR"
            justificativa = f"Elegibilidade baixa ({score['score_final']:.0%}). {politica.justificativa}"
        else:
            acao = "ESCALAR"
            justificativa = f"Caso requer análise adicional. {politica.justificativa}"
        
        return RespostaAgente(
            resposta_final=justificativa,
            confianca=politica.confianca.value,
            acao=acao,
            fontes=fontes,
            codigo_politica=politica.codigo_politica,
            score=score['score_final'],
            detalhes_score=score['scores_parciais'],
            metodo_decisao="combinado"
        )


def carregar_resposta_usuario(caminho_json: str = "resposta_usuario.json") -> Optional[Dict]:
    """Carrega dados do usuário do arquivo JSON."""
    try:
        if not os.path.exists(caminho_json):
            print(f"Arquivo '{caminho_json}' não encontrado.")
            print("Execute primeiro 'python reclamacoes.py' para gerar as respostas.\n")
            return None
        
        with open(caminho_json, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
        
        print(f"Dados do usuário carregados de '{caminho_json}'\n")
        return dados
    
    except json.JSONDecodeError as erro:
        print(f"Erro ao decodificar JSON: {erro}")
        return None
    except Exception as erro:
        print(f"Erro ao carregar arquivo: {erro}")
        return None


def exibir_resultado(resposta: RespostaAgente):
    """Exibe resultado formatado da análise."""
    print("\n" + "="*60)
    print("  RESULTADO DA ANÁLISE")
    print("="*60 + "\n")
    
    # Indicador baseado na decisao
    indicadores = {
        "APROVAR": "[+]",
        "REJEITAR": "[-]",
        "ESCALAR": "[!]",
        "ANALISE_MANUAL": "[?]"
    }
    indicador = indicadores.get(resposta.acao, "[*]")
    
    print(f"{indicador} DECISAO: {resposta.acao}")
    print(f"CONFIANCA: {resposta.confianca}")
    print(f"SCORE: {resposta.score:.1%}")
    print(f"POLITICA: {resposta.codigo_politica}")
    print(f"METODO: {resposta.metodo_decisao}")
    print(f"\nRESPOSTA:")
    print(f"   {resposta.resposta_final}")
    
    if resposta.fontes:
        print(f"\nFONTES CONSULTADAS:")
        for fonte in set(resposta.fontes):
            print(f"   - {fonte}")
    
    if resposta.detalhes_score:
        print(f"\nBREAKDOWN DO SCORE:")
        for fator, valor in resposta.detalhes_score.items():
            print(f"   - {fator}: {valor:.2f}")
    
    print(f"\nTempo de processamento: {resposta.tempo_processamento_ms:.1f}ms")
    print("\n" + "="*60 + "\n")


def executar_modo_interativo():
    """Executa o sistema no modo interativo com dados do usuário."""
    print("\n" + "="*60)
    print("  SISTEMA DE ANÁLISE DE REEMBOLSO - IFOOD v2.0")
    print("="*60 + "\n")
    
    # Configurar logging (modo não-JSON para console limpo)
    configurar_logging(formato_json=False)
    
    agente = AgenteReembolsoV2()
    dados_usuario = carregar_resposta_usuario()
    
    if not dados_usuario:
        print("Não foi possível processar a solicitação.\n")
        return
    
    consulta = dados_usuario.get("consulta_usuario", "")
    contexto = dados_usuario.get("contexto", {})
    
    print("DADOS DA SOLICITACAO:")
    print(f"   Consulta: {consulta}")
    print(f"   Categoria: {contexto.get('categoria', 'N/A')}")
    print(f"   Status: {contexto.get('status', 'N/A')}")
    print(f"   Motivo: {contexto.get('motivo', 'N/A')}")
    
    detalhes = contexto.get('detalhes_adicionais', {})
    if detalhes:
        if detalhes.get('valor_pedido'):
            print(f"   Valor: R$ {detalhes.get('valor_pedido')}")
        if detalhes.get('tempo_espera'):
            print(f"   Tempo de espera: {detalhes.get('tempo_espera')} min")
    
    print("\n" + "-"*60)
    
    resposta = agente.processar_solicitacao(consulta, contexto)
    exibir_resultado(resposta)


def executar_modo_teste():
    """Executa cenários de teste para validar o sistema."""
    print("\n" + "="*60)
    print("  MODO TESTE - CENÁRIOS PREDEFINIDOS v2.0")
    print("="*60 + "\n")
    
    configurar_logging(formato_json=False)
    agente = AgenteReembolsoV2()
    
    cenarios = [
        {
            "nome": "Arrependimento após saída para entrega",
            "consulta": "Quero cancelar, o pedido já saiu mas mudei de ideia",
            "contexto": {
                "status": "SAIU_PARA_ENTREGA",
                "motivo": "ARREPENDIMENTO_CLIENTE",
                "categoria": "reembolso",
                "detalhes_adicionais": {"valor_pedido": "45.90"}
            }
        },
        {
            "nome": "Erro do restaurante",
            "consulta": "Meu pedido veio completamente errado, pedi pizza e veio hambúrguer",
            "contexto": {
                "status": "ENTREGUE",
                "motivo": "ERRO_RESTAURANTE",
                "categoria": "entrega",
                "detalhes_adicionais": {"valor_pedido": "89.00"}
            }
        },
        {
            "nome": "Fraude - Compra não reconhecida",
            "consulta": "Não fiz essa compra, minha conta foi hackeada",
            "contexto": {
                "status": "ENTREGUE",
                "motivo": "COMPRA_NAO_RECONHECIDA",
                "categoria": "fraude",
                "detalhes_adicionais": {"valor_pedido": "250.00"}
            }
        },
        {
            "nome": "Pedido não recebido",
            "consulta": "Meu pedido não chegou mas está marcado como entregue",
            "contexto": {
                "status": "ENTREGUE",
                "motivo": "NAO_RECEBIDO",
                "categoria": "entrega",
                "detalhes_adicionais": {"valor_pedido": "55.00", "tempo_espera": "90"}
            }
        },
        {
            "nome": "Cancelamento antes da confirmação",
            "consulta": "Quero cancelar, ainda não confirmaram",
            "contexto": {
                "status": "AGUARDANDO_CONFIRMACAO",
                "motivo": "ARREPENDIMENTO_CLIENTE",
                "categoria": "reembolso",
                "detalhes_adicionais": {}
            }
        }
    ]
    
    resultados = []
    
    for i, cenario in enumerate(cenarios, 1):
        print(f"\n{'─'*60}")
        print(f"CENÁRIO {i}: {cenario['nome']}")
        print(f"{'─'*60}")
        
        resposta = agente.processar_solicitacao(
            cenario['consulta'], 
            cenario['contexto']
        )
        
        resultados.append({
            "cenario": cenario['nome'],
            "decisao": resposta.acao,
            "confianca": resposta.confianca,
            "score": resposta.score,
            "politica": resposta.codigo_politica
        })
        
        print(f"\n   Resultado:")
        print(f"      Decisao: {resposta.acao}")
        print(f"      Confianca: {resposta.confianca}")
        print(f"      Score: {resposta.score:.1%}")
        print(f"      Politica: {resposta.codigo_politica}")
    
    # Resumo
    print("\n" + "="*60)
    print("  RESUMO DOS TESTES")
    print("="*60 + "\n")
    
    for r in resultados:
        indicador = "[+]" if r['decisao'] in ['APROVAR'] else "[-]" if r['decisao'] == 'REJEITAR' else "[!]"
        print(f"{indicador} {r['cenario'][:35]:<35} | {r['decisao']:<10} | {r['score']:.0%}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    # Verificar argumentos de linha de comando
    if len(sys.argv) > 1 and sys.argv[1] == "--teste":
        executar_modo_teste()
    elif os.path.exists("resposta_usuario.json"):
        print("\nArquivo 'resposta_usuario.json' encontrado!")
        print("   Executando em modo INTERATIVO...\n")
        executar_modo_interativo()
    else:
        print("\nNenhum arquivo de resposta encontrado.")
        print("   Executando em modo TESTE...\n")
        executar_modo_teste()
        print("\nDica: Execute 'python reclamacoes.py' para simular uma reclamação real!")
        print("      Ou use 'python main_v2.py --teste' para rodar os cenários de teste.\n")

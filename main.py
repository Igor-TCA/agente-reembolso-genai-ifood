import csv
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ItemConhecimento:
    categoria: str
    pergunta: str
    resposta: str
    fonte: str

@dataclass
class RespostaAgente:
    resposta_final: str
    confianca: str
    acao: str
    fontes: List[str]

class BaseConhecimento:
    def __init__(self, caminho_csv: str):
        self.itens: List[ItemConhecimento] = []
        self._carregar_dados(caminho_csv)

    def _carregar_dados(self, caminho: str):
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
            print(f"Base de conhecimento carregada: {len(self.itens)} itens do arquivo '{caminho}'")
        except FileNotFoundError:
            print(f"Arquivo '{caminho}' não encontrado. Base de conhecimento vazia.")
        except Exception as erro:
            print(f"Erro ao carregar dados: {erro}")

    def buscar(self, consulta: str) -> List[ItemConhecimento]:
        consulta_minuscula = consulta.lower()
        resultados = []
        for item in self.itens:
            if any(termo in item.pergunta.lower() for termo in consulta_minuscula.split()):
                resultados.append(item)
        return resultados

class MotorPoliticas:
    @staticmethod
    def validar_regras_rigidas(contexto: Dict) -> Optional[str]:
        if contexto.get('status') == 'SAIU_PARA_ENTREGA' and contexto.get('motivo') == 'ARREPENDIMENTO_CLIENTE':
            return "REJEITADO_POLITICA_4_1: Desistência após saída para entrega não é reembolsável."
        
        if contexto.get('status') == 'SAIU_PARA_ENTREGA' and contexto.get('motivo') in ['ERRO_RESTAURANTE', 'ERRO_APP']:
            return "APROVADO_POLITICA_3_2: Falha operacional detectada."
            
        return None

class AgenteReembolso:
    def __init__(self):
        self.bc = BaseConhecimento("base_conhecimento_ifood_genai-exemplo.csv")
        self.motor_politicas = MotorPoliticas()

    def processar_solicitacao(self, consulta_usuario: str, contexto: Dict) -> RespostaAgente:
        print(f"--- Processando: '{consulta_usuario}' ---")
        
        print("[1/4] Realizando busca vetorial...")
        politicas_encontradas = self.bc.buscar(consulta_usuario)
        fontes_consultadas = [d.fonte for d in politicas_encontradas]
        
        print(f"[2/4] Políticas recuperadas: {len(politicas_encontradas)} documentos")
        if not politicas_encontradas:
            print("[!] Nenhuma política encontrada - Escalando para humano")
            return RespostaAgente(
                "Não encontrei informações suficientes na base de conhecimento.", 
                "Baixa", 
                "ESCALAR", 
                []
            )

        print("[3/4] Aplicando regras determinísticas...")
        decisao_regra_rigida = self.motor_politicas.validar_regras_rigidas(contexto)
        
        if decisao_regra_rigida:
            if "REJEITADO" in decisao_regra_rigida:
                print("[✓] Regra de Bloqueio Ativada - Rejeição Automática")
                return RespostaAgente(
                    "Solicitação negada automaticamente com base na política de entrega.", 
                    "Alta", 
                    "REJEITAR", 
                    fontes_consultadas
                )
            if "APROVADO" in decisao_regra_rigida:
                print("[✓] Regra de Aprovação Ativada - Aprovação Automática")
                return RespostaAgente(
                    "Solicitação aprovada automaticamente por falha operacional.", 
                    "Alta", 
                    "APROVAR", 
                    fontes_consultadas
                )

        print("[4/4] Regra inconclusiva - Acionando IA Generativa...")
        resposta_ia = self._analisar_com_ia(politicas_encontradas, consulta_usuario, contexto)
        return resposta_ia
    
    def _analisar_com_ia(self, documentos: List[ItemConhecimento], consulta: str, contexto: Dict) -> RespostaAgente:
        fontes = [d.fonte for d in documentos]
        palavras_chave_criticas = ['cancelar', 'reembolso', 'erro', 'problema']
        nivel_confianca = sum(1 for palavra in palavras_chave_criticas if palavra in consulta.lower())
        
        if nivel_confianca >= 2:
            print("[IA] Alta Confiança - Gerando resposta")
            resumo_politicas = " ".join([f"{d.pergunta}: {d.resposta}" for d in documentos[:2]])
            return RespostaAgente(
                f"Com base nas políticas consultadas, recomendo análise detalhada. Contexto: {resumo_politicas[:150]}...",
                "Alta",
                "ESCALAR",
                fontes
            )
        else:
            print("[IA] Baixa Confiança - Fallback Humano")
            return RespostaAgente(
                f"Caso complexo identificado. Encaminhando para análise humana especializada. Fontes consultadas: {', '.join(set(fontes))}",
                "Baixa",
                "ESCALAR",
                fontes
            )

def carregar_resposta_usuario(caminho_json: str = "resposta_usuario.json") -> Optional[Dict]:
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


def executar_modo_interativo():
    print("\n" + "="*60)
    print("  SISTEMA DE ANÁLISE DE REEMBOLSO - IFOOD")
    print("="*60 + "\n")
    
    agente = AgenteReembolso()
    dados_usuario = carregar_resposta_usuario()
    
    if not dados_usuario:
        print("Não foi possível processar a solicitação.\n")
        return
    
    consulta = dados_usuario.get("consulta_usuario", "")
    contexto = dados_usuario.get("contexto", {})
    
    print("DADOS DA SOLICITAÇÃO:")
    print(f"   Consulta: {consulta}")
    print(f"   Categoria: {contexto.get('categoria', 'N/A')}")
    print(f"   Status: {contexto.get('status', 'N/A')}")
    print(f"   Motivo: {contexto.get('motivo', 'N/A')}")
    
    if contexto.get('detalhes_adicionais'):
        print(f"   Detalhes: {contexto.get('detalhes_adicionais')}")
    
    print("\n" + "-"*60 + "\n")
    
    resposta = agente.processar_solicitacao(consulta, contexto)
    
    print("\n" + "="*60)
    print("  RESULTADO DA ANÁLISE")
    print("="*60 + "\n")
    print(f"DECISÃO: {resposta.acao}")
    print(f"CONFIANÇA: {resposta.confianca}")
    print(f"RESPOSTA: {resposta.resposta_final}")
    
    if resposta.fontes:
        print(f"\nFONTES CONSULTADAS:")
        for fonte in set(resposta.fontes):
            print(f"   • {fonte}")
    
    print("\n" + "="*60 + "\n")


def executar_modo_teste():
    print("\n" + "="*60)
    print("  MODO TESTE - CENÁRIOS PREDEFINIDOS")
    print("="*60 + "\n")
    
    agente = AgenteReembolso()

    print("CENÁRIO 1: Arrependimento do cliente")
    contexto_arrependimento = {
        "status": "SAIU_PARA_ENTREGA",
        "motivo": "ARREPENDIMENTO_CLIENTE"
    }
    resposta = agente.processar_solicitacao("Quero cancelar, o pedido já saiu mas mudei de ideia", contexto_arrependimento)
    print(f"   Decisão: {resposta.acao} | Motivo: {resposta.resposta_final}\n")

    print("CENÁRIO 2: Erro do restaurante")
    contexto_erro = {
        "status": "SAIU_PARA_ENTREGA",
        "motivo": "ERRO_RESTAURANTE"
    }
    resposta2 = agente.processar_solicitacao("Veio errado, o pedido saiu agora", contexto_erro)
    print(f"   Decisão: {resposta2.acao} | Motivo: {resposta2.resposta_final}\n")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    if os.path.exists("resposta_usuario.json"):
        print("\nArquivo 'resposta_usuario.json' encontrado!")
        print("   Executando em modo INTERATIVO...\n")
        executar_modo_interativo()
    else:
        print("\nNenhum arquivo de resposta encontrado.")
        print("   Executando em modo TESTE...\n")
        executar_modo_teste()
        print("\nDica: Execute 'python reclamacoes.py' para simular uma reclamação real!\n")
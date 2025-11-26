"""
Módulo para gerenciamento de arquivos JSON.
Responsável por salvar e carregar dados em formato JSON.
"""
import json
from typing import Dict, Optional


class GerenciadorJSON:
    @staticmethod
    def salvar(dados: Dict, caminho_arquivo: str) -> bool:
        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            
            print(f"\nRespostas salvas em '{caminho_arquivo}'")
            print("\nProcessando sua solicitação...\n")
            return True
        except Exception as erro:
            print(f"\nErro ao salvar arquivo: {erro}")
            return False
    
    @staticmethod
    def carregar(caminho_arquivo: str) -> Optional[Dict]:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                dados = json.load(arquivo)
            return dados
        except FileNotFoundError:
            print(f"\nArquivo '{caminho_arquivo}' não encontrado.")
            return None
        except json.JSONDecodeError as erro:
            print(f"\nErro ao decodificar JSON: {erro}")
            return None
        except Exception as erro:
            print(f"\nErro ao carregar arquivo: {erro}")
            return None

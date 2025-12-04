"""
Módulo de utilitários para interface de usuário.
Funções auxiliares para interação no terminal.
"""
import os
from typing import List


def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


def exibir_cabecalho(titulo: str):
    print("\n" + "="*60)
    print(f"  {titulo}")
    print("="*60 + "\n")


def exibir_separador():
    print("-"*60)


def solicitar_opcao(pergunta: str, opcoes: List[str]) -> int:
    print(pergunta)
    print()
    
    for idx, opcao in enumerate(opcoes, 1):
        print(f"  [{idx}] {opcao}")
    print()
    
    while True:
        try:
            escolha = int(input("Digite o número da sua opção: "))
            if 1 <= escolha <= len(opcoes):
                return escolha
            else:
                print(f"Por favor, escolha um número entre 1 e {len(opcoes)}")
        except ValueError:
            print("Por favor, digite um número válido")


def solicitar_confirmacao(mensagem: str = "Confirma as informações? (S/N): ") -> bool:
    resposta = input(mensagem).strip().upper()
    return resposta == 'S'


def solicitar_entrada(mensagem: str, opcional: bool = False) -> str:
    while True:
        entrada = input(mensagem).strip()
        if entrada or opcional:
            return entrada
        print("Este campo é obrigatório. Por favor, digite algo.")
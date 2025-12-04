#!/usr/bin/env python
"""
Script de entrada para o sistema de coleta de reclamacoes.
Execute este arquivo para iniciar a interface de coleta.
"""
import sys
import os

# Adicionar o diretorio raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.reclamacoes import SistemaReclamacoes

if __name__ == "__main__":
    sistema = SistemaReclamacoes()
    sistema.executar()

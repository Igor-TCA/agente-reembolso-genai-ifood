# Frontend - Interface de coleta de reclamacoes
from .reclamacoes import SistemaReclamacoes
from .modelos_dados import MapeamentoCategoria, MapeamentoStatus, MapeamentoMotivo, OpcoesMenu, TemplatesConsulta, criar_contexto_vazio
from .gerenciador_json import GerenciadorJSON
from .utils_interface import limpar_tela, exibir_cabecalho, exibir_separador, solicitar_opcao, solicitar_confirmacao, solicitar_entrada

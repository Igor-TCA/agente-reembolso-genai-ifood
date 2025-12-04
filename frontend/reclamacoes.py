"""
Sistema de coleta de reclamações do iFood.
Módulo principal que orquestra o fluxo de coleta de informações do usuário.
"""
from typing import Dict

from .utils_interface import (
    limpar_tela, 
    exibir_cabecalho, 
    exibir_separador,
    solicitar_opcao,
    solicitar_confirmacao,
    solicitar_entrada
)
from .modelos_dados import (
    MapeamentoCategoria,
    MapeamentoStatus,
    MapeamentoMotivo,
    OpcoesMenu,
    TemplatesConsulta,
    criar_contexto_vazio
)
from .gerenciador_json import GerenciadorJSON


class SistemaReclamacoes:
    def __init__(self):
        self.respostas_usuario: Dict = criar_contexto_vazio()
        self.gerenciador_json = GerenciadorJSON()
    
    def coletar_tipo_problema(self) -> int:
        limpar_tela()
        exibir_cabecalho("ATENDIMENTO IFOOD - Qual é o seu problema?")
        
        escolha = solicitar_opcao(
            "Selecione o tipo de problema:", 
            OpcoesMenu.TIPO_PROBLEMA
        )
        
        self.respostas_usuario["contexto"]["categoria"] = MapeamentoCategoria.OPCOES[escolha]
        return escolha
    
    def coletar_status_pedido(self):
        limpar_tela()
        exibir_cabecalho("ATENDIMENTO IFOOD - Status do Pedido")
        
        escolha = solicitar_opcao(
            "Qual o status atual do seu pedido?", 
            OpcoesMenu.STATUS_PEDIDO
        )
        
        self.respostas_usuario["contexto"]["status"] = MapeamentoStatus.OPCOES[escolha]
    
    def coletar_motivo_problema(self, tipo_problema: int):
        limpar_tela()
        exibir_cabecalho("ATENDIMENTO IFOOD - Motivo do Problema")
        
        opcoes = OpcoesMenu.obter_opcoes_motivo(tipo_problema)
        mapeamento = MapeamentoMotivo.obter_por_tipo(tipo_problema)
        
        escolha = solicitar_opcao("Qual o motivo específico?", opcoes)
        self.respostas_usuario["contexto"]["motivo"] = mapeamento[escolha]
    
    def coletar_detalhes_adicionais(self):
        limpar_tela()
        exibir_cabecalho("ATENDIMENTO IFOOD - Detalhes Adicionais")
        
        print("Por favor, descreva brevemente o que aconteceu:")
        print("(Isso ajudará nosso sistema a entender melhor seu caso)\n")
        
        descricao = solicitar_entrada("Sua descrição: ", opcional=True)
        
        if descricao:
            self.respostas_usuario["consulta_usuario"] = descricao
        else:
            self.respostas_usuario["consulta_usuario"] = self._gerar_consulta_padrao()
        
        self._coletar_informacoes_complementares()
    
    def _gerar_consulta_padrao(self) -> str:
        motivo = self.respostas_usuario["contexto"]["motivo"]
        categoria = self.respostas_usuario["contexto"]["categoria"]
        
        return TemplatesConsulta.obter_template(motivo, categoria)
    
    def _coletar_informacoes_complementares(self):
        print("\nInformações complementares (opcional):")
        valor_pedido = solicitar_entrada("Valor do pedido (R$): ", opcional=True)
        tempo_espera = solicitar_entrada("Tempo de espera (em minutos): ", opcional=True)
        
        if valor_pedido:
            self.respostas_usuario["contexto"]["detalhes_adicionais"]["valor_pedido"] = valor_pedido
        if tempo_espera:
            self.respostas_usuario["contexto"]["detalhes_adicionais"]["tempo_espera"] = tempo_espera
    
    def exibir_resumo_confirmacao(self) -> bool:
        limpar_tela()
        exibir_cabecalho("ATENDIMENTO IFOOD - Confirmação")
        
        print("RESUMO DA SUA SOLICITAÇÃO:\n")
        print(f"  Categoria: {self.respostas_usuario['contexto']['categoria']}")
        print(f"  Status do Pedido: {self.respostas_usuario['contexto']['status']}")
        print(f"  Motivo: {self.respostas_usuario['contexto']['motivo']}")
        print(f"  Descrição: {self.respostas_usuario['consulta_usuario']}")
        
        if self.respostas_usuario['contexto']['detalhes_adicionais']:
            print(f"  Detalhes Adicionais: {self.respostas_usuario['contexto']['detalhes_adicionais']}")
        
        print()
        exibir_separador()
        
        return solicitar_confirmacao("\nConfirma as informações? (S/N): ")
    
    def salvar_respostas(self, caminho_arquivo: str = "resposta_usuario.json") -> bool:
        return self.gerenciador_json.salvar(self.respostas_usuario, caminho_arquivo)
    
    def reiniciar_respostas(self):
        self.respostas_usuario = criar_contexto_vazio()
    
    def exibir_conclusao(self):
        limpar_tela()
        exibir_cabecalho("ATENDIMENTO CONCLUÍDO")
        print("Suas informações foram registradas com sucesso!")
        print("\nArquivo gerado: resposta_usuario.json")
        print("\nPróximo passo: Execute 'python main.py' para processar sua solicitação")
        print("\n" + "="*60 + "\n")
    
    def executar(self):
        print("\nBem-vindo ao Sistema de Atendimento iFood!\n")
        input("Pressione ENTER para iniciar...")
        
        while True:
            tipo_problema = self.coletar_tipo_problema()
            self.coletar_status_pedido()
            self.coletar_motivo_problema(tipo_problema)
            self.coletar_detalhes_adicionais()
            
            if self.exibir_resumo_confirmacao():
                break
            else:
                print("\nVamos recomeçar...\n")
                input("Pressione ENTER para continuar...")
                self.reiniciar_respostas()
        
        if self.salvar_respostas():
            self.exibir_conclusao()


if __name__ == "__main__":
    sistema = SistemaReclamacoes()
    sistema.executar()
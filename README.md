# POC: Agente de Reembolso Inteligente (Híbrido)

Este projeto é uma Prova de Conceito (POC) de um agente de IA para automação de decisões de reembolso, utilizando uma arquitetura híbrida que combina **RAG** para interpretação de políticas e **Python** para validação de regras de negócio críticas.

---
## Arquitetura

1.  **Camada de Conhecimento (RAG):** Busca semântica para entender nuances de texto.
2.  **Camada Determinística (Code):** Regras de "Hard Block" para compliance financeiro.
3.  **Camada de Orquestração:** Gerencia o fluxo e o fallback.

---
### Fluxo de Decisão
```mermaid
flowchart TD

    A[Input Usuário] --> B{Busca Vetorial}
    B --> C[Recuperar Políticas Relevantes]
    C --> D{Validação Rígida}
    D -- "Regra de Bloqueio Ativada" --> E[Rejeição Automática]
    D -- "Regra de Aprovação Ativada" --> F[Aprovação Automática]
    D -- "Regra inconclusiva" --> G{IA Generativa}
    G -- "Alta Confiança" --> H[Resposta da IA]
    G -- "Baixa Confiança" --> I[Fallback Humano]
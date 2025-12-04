# (POC GenAI iFood) Agente de Reembolso Inteligente - Arquitetura Híbrida V2.0

Sistema inteligente de analise e processamento de solicitacoes de reembolso para o iFood, utilizando tecnicas avancadas de IA e processamento de linguagem natural.

## Novidades da Versao 2.0

- **Busca Semantica**: TF-IDF com expansao de sinonimos para melhor recuperacao de politicas
- **Motor de Politicas Expandido**: +16 regras deterministicas cobrindo mais cenarios
- **Sistema de Scoring**: Pontuacao transparente baseada em multiplos fatores
- **Integracao LLM Real**: Suporte a OpenAI GPT e Google Gemini com fallback local
- **Logging Estruturado**: Auditoria completa de todas as decisoes
- **Tratamento de Erros**: Sistema robusto com recuperacao de falhas
- **Testes Unitarios**: Cobertura de testes para garantir qualidade

## Estrutura do Projeto

```
MyProject/
├── main.py                     # Agente principal v2.0
├── coletar_reclamacao.py       # Script para coletar reclamacoes (CLI)
├── backend/                    # Motor de processamento
│   ├── motor_politicas.py      # Motor de regras (16 regras) + Scoring
│   ├── busca_semantica.py      # Busca TF-IDF com sinonimos
│   ├── integracao_llm.py       # Integracao OpenAI/Gemini/Local
│   ├── sistema_logging.py      # Logging estruturado
│   └── tratamento_erros.py     # Tratamento de excecoes
├── frontend/                   # Interface CLI do usuario
│   ├── reclamacoes.py          # Coleta de reclamacoes
│   ├── modelos_dados.py        # Modelos e mapeamentos
│   ├── gerenciador_json.py     # Persistencia de dados
│   └── utils_interface.py      # Utilitarios de interface
├── web/                        # Interface Web (HTML/CSS/JS)
│   ├── index.html              # Pagina principal
│   ├── styles.css              # Estilos (tema vermelho/branco/preto)
│   └── app.js                  # Logica da interface
├── tests/                      # Testes unitarios
│   └── tests.py
├── base_conhecimento_*.csv     # Base de politicas
└── logs/                       # Arquivos de auditoria (gerados)
```

## Como Usar

### 1. Interface Web (recomendado)

Abra o arquivo `web/index.html` no navegador para usar a interface grafica.

### 2. Modo CLI Interativo (com reclamacao do usuario)

```bash
# Primeiro, colete a reclamacao do usuario
python coletar_reclamacao.py

# Depois, processe com o agente
python main.py
```

### 2. Modo Teste (cenarios predefinidos)

```bash
python main.py --teste
```

### 3. Executar Testes Unitários

```bash
python tests/tests.py
```

## Pipeline de Processamento

```
+-------------------------------------------------------------+
|                    PIPELINE v2.0                            |
+-------------------------------------------------------------+
|  1. Busca Semantica (TF-IDF + Sinonimos)                    |
|     -> Recupera politicas relevantes da base de conhecimento|
+-------------------------------------------------------------+
|  2. Motor de Politicas (16 regras)                          |
|     -> Aplica regras deterministicas                        |
+-------------------------------------------------------------+
|  3. Sistema de Scoring                                      |
|     -> Calcula elegibilidade baseada em multiplos fatores   |
+-------------------------------------------------------------+
|  4. Analise LLM (se necessario)                             |
|     -> OpenAI/Gemini/Local para casos complexos             |
+-------------------------------------------------------------+
|  5. Decisao Final                                           |
|     -> APROVAR | REJEITAR | ESCALAR | ANALISE_MANUAL        |
+-------------------------------------------------------------+
```

## Regras de Politica Implementadas

| Codigo | Descricao | Decisao |
|--------|-----------|---------|
| FRAUDE_F1 | Compra nao reconhecida | Analise Manual |
| FRAUDE_F2 | Conta comprometida | Analise Manual |
| FRAUDE_F3 | Multiplas cobrancas | Analise Manual |
| CANCELAMENTO_C1 | Restaurante cancelou | Aprovar |
| CANCELAMENTO_C2 | Erro do app | Aprovar |
| CANCELAMENTO_C3 | Antes da confirmacao | Aprovar |
| ERRO_E1 | Erro do restaurante | Aprovar |
| ERRO_E2 | Erro do entregador | Aprovar |
| ENTREGA_D1 | Pedido nao recebido | Aprovar/Manual |
| ENTREGA_D2 | Pedido incompleto | Aprovar |
| FINANCEIRO_FIN1 | Cobranca duplicada | Aprovar |
| FINANCEIRO_FIN2 | Cobranca pos-cancelamento | Aprovar |
| ATRASO_A1 | Atraso excessivo | Aprovar/Escalar |
| ARREPENDIMENTO_R1 | Antes do preparo | Aprovar |
| ARREPENDIMENTO_R2 | Apos saida entrega | Rejeitar |
| VALOR_V1 | Alto valor (>R$300) | Analise Manual |

## Sistema de Scoring

O score e calculado considerando:

- **Tipo de Problema** (25%): Categoria da reclamacao
- **Valor do Pedido** (15%): Risco baseado no valor
- **Status do Pedido** (15%): Fase atual do pedido
- **Motivo** (25%): Elegibilidade do motivo
- **Politica Aplicada** (20%): Resultado das regras

### Recomendacoes baseadas no score:

| Score | Recomendacao |
|-------|--------------|
| >= 0.8 | APROVAR - Alta confianca |
| >= 0.6 | APROVAR_COM_ANALISE - Validacao adicional |
| >= 0.4 | ESCALAR - Analise humana |
| < 0.4 | REJEITAR - Baixa elegibilidade |

## Exemplo de Saida

```
============================================================
  RESULTADO DA ANALISE
============================================================

[+] DECISAO: APROVAR
CONFIANCA: Alta
SCORE: 95.0%
POLITICA: ERRO_E1
METODO: politica

RESPOSTA:
   Erro do restaurante confirmado. Reembolso total aprovado conforme Politica 2.1.

FONTES CONSULTADAS:
   - Politica 2.1
   - Politica 3.2

BREAKDOWN DO SCORE:
   - tipo_problema: 0.70
   - valor_pedido: 0.90
   - status_pedido: 0.30
   - motivo: 0.95
   - politica: 0.95

Tempo de processamento: 45.2ms
============================================================
```

## Auditoria e Logging

Todos os processamentos sao registrados em:
- **Console**: Formato legivel com formatacao
- **Arquivo JSON**: `logs/auditoria_YYYYMMDD_HHMMSS.jsonl` (formato estruturado)

### Tipos de eventos registrados:
- Início/fim de processamento
- Busca na base de conhecimento
- Aplicação de políticas
- Cálculo de scores
- Análises por LLM
- Decisões finais
- Erros e exceções

## Requisitos

### Obrigatorios
- Python 3.8+

### Opcionais (para integracao LLM)
```bash
pip install openai            # Para OpenAI GPT
pip install google-generativeai  # Para Google Gemini
```

## Testes

Execute os testes unitarios para validar o sistema:

```bash
python tests.py
```

### Cobertura de testes:
- Motor de Politicas (7 testes)
- Sistema de Scoring (3 testes)
- Processador de Texto (3 testes)
- Motor TF-IDF (3 testes)
- Analisador Local (4 testes)
- Integracao (2 testes)

## Comparativo: v1.0 vs v2.0

| Funcionalidade | v1.0 | v2.0 |
|----------------|------|------|
| Busca na base | Palavras-chave simples | TF-IDF + Sinonimos |
| Regras de politica | 2 | 16 |
| Sistema de scoring | Nao | Transparente |
| Integracao LLM | Simulado | OpenAI/Gemini/Local |
| Logging | Print simples | Estruturado + Auditoria |
| Tratamento de erros | Basico | Robusto com fallback |
| Testes | Nao | 22 testes |
| Uso de contexto | Parcial | Completo |

## Licenca

Projeto educacional para demonstracao de tecnicas de GenAI aplicadas a atendimento ao cliente.

---

**Desenvolvido como POC para o desafio iFood GenAI**

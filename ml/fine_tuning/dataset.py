"""Dataset de instrução para o fine-tuning do assistente de retenção.

Domínio: Customer Intelligence do Argus — o mesmo domínio de negócio do
resto do projeto (churn, ações de retenção, políticas). Pequeno e sintético
de propósito: o objetivo deste módulo é demonstrar o **mecanismo** de
fine-tuning (LoRA/QLoRA) de ponta a ponta, não treinar um modelo de
produção — isso exigiria um dataset real, muito maior, e um ciclo de
avaliação humano.

Formato: pares (prompt, completion) no chat template do modelo-base
(`tokenizer.apply_chat_template`), grounded nos mesmos conceitos que
`ml/churn/`, `ml/reinforcement/next_best_action.py` e
`data/documents/templates/refund_policy.md` já usam no restante do projeto.
"""
from __future__ import annotations

SYSTEM_PROMPT = (
    "Você é o assistente de retenção do Argus. Responda de forma curta, "
    "objetiva e baseada nos dados do cliente."
)

TRAIN_EXAMPLES: list[dict] = [
    {
        "prompt": "Cliente com churn_score 0.81, 4 tickets de suporte nos últimos 30 dias "
                  "e uso do produto caindo 40%. Qual ação de retenção recomendar?",
        "completion": "Risco alto (0.81). Recomendo contato humano prioritário + oferta de "
                       "desconto de retenção, já que o padrão (tickets altos + uso em queda) "
                       "indica frustração recente, não apenas preço.",
    },
    {
        "prompt": "Cliente com churn_score 0.22, sem tickets de suporte, uso estável. "
                  "Qual ação de retenção recomendar?",
        "completion": "Risco baixo (0.22). Nenhuma ação de retenção necessária agora; "
                       "manter no fluxo padrão de engajamento (recomendação de produto).",
    },
    {
        "prompt": "Explique por que um cliente com muitos tickets de suporte tende a ter "
                  "churn_score mais alto.",
        "completion": "Tickets de suporte frequentes normalmente indicam atrito não resolvido "
                       "com o produto; o modelo aprendeu essa correlação a partir do histórico "
                       "de clientes que cancelaram após múltiplos contatos de suporte.",
    },
    {
        "prompt": "Um cliente pergunta em quantos dias pode solicitar reembolso.",
        "completion": "De acordo com a política de reembolso vigente, o prazo padrão é de 30 "
                       "dias corridos a partir da data da compra, mediante nota fiscal.",
    },
    {
        "prompt": "Cliente com churn_score 0.55, aumento recente no uso, mas 2 tickets abertos "
                   "sem resposta. Qual ação recomendar?",
        "completion": "Risco médio (0.55) com sinal misto: engajamento subindo, mas suporte "
                       "pendente pode reverter isso. Recomendo resolver os tickets em aberto "
                       "antes de qualquer oferta comercial.",
    },
    {
        "prompt": "Qual a diferença entre a ação de retenção para um cliente de alto valor "
                   "(LTV alto) e um de baixo valor, ambos com churn_score 0.75?",
        "completion": "Mesmo risco, tratamento proporcional ao LTV: cliente de alto valor "
                       "recebe contato humano + oferta personalizada; cliente de baixo valor "
                       "recebe campanha automatizada de engajamento, para manter o custo de "
                       "retenção proporcional ao valor do cliente.",
    },
    {
        "prompt": "Resuma em uma frase o que o churn_score representa.",
        "completion": "O churn_score é a probabilidade estimada, entre 0 e 1, de o cliente "
                       "cancelar o serviço nos próximos 30 dias, segundo o modelo de churn.",
    },
    {
        "prompt": "Cliente pergunta como funciona a garantia do produto.",
        "completion": "A garantia cobre defeitos de fabricação por 12 meses a partir da compra; "
                       "para acioná-la, é necessário apresentar a nota fiscal e o número de série.",
    },
]

# held-out (não usados no treino) — servem para o eval qualitativo do módulo
EVAL_PROMPTS: list[str] = [
    "Cliente com churn_score 0.90, 6 tickets de suporte, uso caindo 60%. O que fazer?",
    "O que é churn_score?",
    "Cliente pergunta sobre o prazo de reembolso.",
]


def to_chat_messages(example: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": example["prompt"]},
        {"role": "assistant", "content": example["completion"]},
    ]

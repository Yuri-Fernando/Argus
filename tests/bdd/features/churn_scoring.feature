# language: pt
Funcionalidade: Scoring de churn dispara evento de retenção
  Como plataforma de Customer Intelligence
  Quero publicar um evento de risco quando um cliente cruza o limiar de churn
  Para que o time de retenção possa agir a tempo

  Cenário: Cliente de alto risco produz evento de retenção
    Dado um cliente com uso em queda e múltiplos incidentes de suporte recentes
    Quando o modelo de churn avalia o cliente
    Então a probabilidade de churn deve exceder o limiar configurado
    E um evento "customer.churn.risk_detected" deve ser publicado no bus

  Cenário: Cliente saudável não gera evento
    Dado um cliente engajado sem incidentes de suporte
    Quando o modelo de churn avalia o cliente
    Então a probabilidade de churn deve ficar abaixo do limiar configurado
    E nenhum evento de retenção deve ser publicado

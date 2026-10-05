"""
agente.py — Camada de agente/intenção (esqueleto, ainda não usado).

No futuro, é aqui que a A.R.I.A. vai olhar pra mensagem do usuário e
decidir se é conversa normal, um pedido envolvendo arquivo, ou uma
automação/ferramenta — encaminhando pro módulo certo:

    Usuário → agente.py → conversação (ai_client) / arquivos / ferramentas

Por enquanto isso ainda não existe: a interface (ui.py) continua
falando direto com core.ai_client, exatamente como antes. Este
arquivo só reserva o lugar pro próximo passo, quando o roteamento de
intenção for implementado de verdade.
"""

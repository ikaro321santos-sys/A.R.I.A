"""
permissoes.py — Esqueleto da camada de permissões (ainda não usado).

Regra do projeto: nenhuma ação potencialmente destrutiva ou
irreversível deve rodar sem confirmação explícita do usuário. Quando
as primeiras ferramentas/automações forem implementadas, elas devem
passar por uma função de confirmação daqui antes de executar —
algo como:

    if permissoes.confirmar("Apagar o arquivo X?"):
        ferramenta.executar()

Por enquanto não existe nenhuma ferramenta no projeto, então este
arquivo só reserva o lugar.
"""

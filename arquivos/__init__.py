"""Pacote arquivos — leitura de anexos por tipo de arquivo.

manager.py identifica o formato e chama o handler certo. Hoje só
existe txt_handler (texto puro); pdf_handler, docx_handler,
planilha_handler e imagem_handler entram aqui depois, cada um em seu
próprio módulo, sem precisar mexer no manager nem na interface."""

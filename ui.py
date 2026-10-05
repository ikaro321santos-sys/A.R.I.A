"""
ui.py — Interface de chat da A.R.I.A. (estilo ChatGPT)

Barra lateral à esquerda: botão "Novo chat" + lista de conversas salvas.
Área de chat à direita: histórico em bolhas selecionáveis/copiáveis
(usuário à direita, A.R.I.A. à esquerda), anexo de arquivo de texto,
indicador de "processando" e campo de mensagem. As respostas chegam em
streaming — palavra por palavra.
"""

import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import ttkbootstrap as tb

from core import ai_client, memoria
from arquivos import manager as arquivos_manager
from voz import captura, fala, reconhecimento
from voz import captura, fala, reconhecimento

# Paleta
COR_FUNDO = "#0d1117"
COR_SIDEBAR = "#161b22"
COR_ITEM_SELECIONADO = "#21262d"
COR_TEXTO_SIDEBAR = "#94a3b8"
COR_BOLHA_USUARIO = "#2563eb"
COR_TEXTO_USUARIO = "#ffffff"
COR_BOLHA_ARIA = "#1e293b"
COR_TEXTO_ARIA = "#e2e8f0"

LARGURA_MAX_BOLHA = 48  # caracteres — bolhas maiores que isso quebram linha
FONTE = ("", 11)  # levemente maior que o padrão do sistema (~9-10pt)

EXTENSOES_TEXTO = [
    ("Arquivos de texto", " ".join(f"*{ext}" for ext in sorted(arquivos_manager.EXTENSOES_TEXTO))),
    ("Todos os arquivos", "*.*"),
]


class ChatApp(tb.Window):
    def __init__(self):
        super().__init__(title="A.R.I.A.", themename="darkly", size=(760, 680))
        self.configure(bg=COR_FUNDO)

        self._anexos_atuais = []  # lista de {"nome": str, "conteudo": str}
        self._gravador = captura.Gravador()
        self._voz_ativa = False  # se True, a A.R.I.A. fala as respostas em voz alta
        self._gravador = captura.Gravador()
        self._voz_ativa = False  # se True, a A.R.I.A. fala as respostas em voz alta

        chats_existentes = memoria.listar_chats()
        self.chat_atual = chats_existentes[0] if chats_existentes else memoria.novo_chat_id()

        self._build_widgets()
        self._atualizar_lista_chats()
        self._carregar_historico()

    # ---------- construção da interface ----------

    def _build_widgets(self):
        container = tk.Frame(self, bg=COR_FUNDO)
        container.pack(fill="both", expand=True)

        self._build_sidebar(container)
        self._build_chat_area(container)

    def _build_sidebar(self, container):
        sidebar = tk.Frame(container, bg=COR_SIDEBAR, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        botao_novo = tk.Button(
            sidebar,
            text="+ Novo chat",
            command=self._novo_chat,
            bg=COR_BOLHA_USUARIO,
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=8,
        )
        botao_novo.pack(fill="x", padx=10, pady=10)

        lista_frame = tk.Frame(sidebar, bg=COR_SIDEBAR)
        lista_frame.pack(fill="both", expand=True)

        self._lista_canvas = tk.Canvas(lista_frame, bg=COR_SIDEBAR, highlightthickness=0)
        lista_scroll = tk.Scrollbar(lista_frame, orient="vertical", command=self._lista_canvas.yview)

        self._lista_chats_frame = tk.Frame(self._lista_canvas, bg=COR_SIDEBAR)
        self._lista_chats_frame.bind(
            "<Configure>",
            lambda evento: self._lista_canvas.configure(scrollregion=self._lista_canvas.bbox("all")),
        )
        janela_lista = self._lista_canvas.create_window(
            (0, 0), window=self._lista_chats_frame, anchor="nw"
        )
        self._lista_canvas.bind(
            "<Configure>",
            lambda evento: self._lista_canvas.itemconfig(janela_lista, width=evento.width),
        )
        self._lista_canvas.configure(yscrollcommand=lista_scroll.set)

        self._lista_canvas.pack(side="left", fill="both", expand=True)
        lista_scroll.pack(side="right", fill="y")

        self._vincular_rolagem(self._lista_canvas, self._lista_canvas)
        self._vincular_rolagem(self._lista_chats_frame, self._lista_canvas)

    def _build_chat_area(self, container):
        chat_area = tk.Frame(container, bg=COR_FUNDO)
        chat_area.pack(side="left", fill="both", expand=True)

        historico_frame = tk.Frame(chat_area, bg=COR_FUNDO)
        historico_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self.canvas = tk.Canvas(historico_frame, bg=COR_FUNDO, highlightthickness=0)
        scrollbar = tb.Scrollbar(historico_frame, orient="vertical", command=self.canvas.yview)

        self.mensagens_frame = tk.Frame(self.canvas, bg=COR_FUNDO)
        self.mensagens_frame.bind(
            "<Configure>",
            lambda evento: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self._janela_interna = self.canvas.create_window(
            (0, 0), window=self.mensagens_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda evento: self.canvas.itemconfig(self._janela_interna, width=evento.width),
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", lambda evento: self.canvas.yview_scroll(int(-1 * (evento.delta / 120)), "units"))
        self.canvas.bind_all("<Button-4>", lambda evento: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda evento: self.canvas.yview_scroll(1, "units"))

        self.status_label = tb.Label(chat_area, text="", bootstyle="secondary")
        self.status_label.pack(fill="x", padx=10)

        # Indicador de anexo — só aparece quando há um arquivo selecionado
        self.anexo_label = tk.Label(
            chat_area,
            text="",
            bg=COR_ITEM_SELECIONADO,
            fg="#e2e8f0",
            anchor="w",
            padx=10,
            pady=4,
            cursor="hand2",
            font=FONTE,
        )
        self.anexo_label.bind("<Button-1>", self._remover_anexo)

        self.entrada_frame = tb.Frame(chat_area)
        self.entrada_frame.pack(fill="x", padx=10, pady=10)

        self.botao_anexar = tb.Button(
            self.entrada_frame, text="📎", command=self._anexar_arquivo, bootstyle="secondary", width=3
        )
        self.botao_anexar.pack(side="left", padx=(0, 5))

        self.botao_microfone = tb.Button(
            self.entrada_frame, text="🎤", bootstyle="secondary", width=3
        )
        self.botao_microfone.pack(side="left", padx=(0, 5))
        self.botao_microfone.bind("<ButtonPress-1>", self._iniciar_gravacao)
        self.botao_microfone.bind("<ButtonRelease-1>", self._parar_gravacao)

        self.botao_voz = tb.Button(
            self.entrada_frame, text="🔇", command=self._alternar_voz, bootstyle="secondary", width=3
        )
        self.botao_voz.pack(side="left", padx=(0, 5))

        self.campo_mensagem = tb.Entry(self.entrada_frame, font=FONTE)
        self.campo_mensagem.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.campo_mensagem.bind("<Return>", lambda evento: self._enviar())

        self.botao_enviar = tb.Button(
            self.entrada_frame, text="Enviar", command=self._enviar, bootstyle="success"
        )
        self.botao_enviar.pack(side="right")

        self.campo_mensagem.focus()

    def _vincular_rolagem(self, widget, canvas):
        """Liga a rodinha do mouse a um canvas específico (evita conflito
        entre a rolagem da barra lateral e a do histórico de mensagens)."""
        widget.bind("<MouseWheel>", lambda evento: canvas.yview_scroll(int(-1 * (evento.delta / 120)), "units"))
        widget.bind("<Button-4>", lambda evento: canvas.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda evento: canvas.yview_scroll(1, "units"))

    # ---------- anexos ----------

    def _anexar_arquivo(self):
        caminhos = filedialog.askopenfilenames(
            title="Selecionar arquivo(s) para anexar", filetypes=EXTENSOES_TEXTO
        )
        if not caminhos:
            return

        for caminho in caminhos:
            try:
                conteudo = arquivos_manager.ler_arquivo(caminho)
            except (OSError, UnicodeDecodeError, ValueError) as erro:
                self.status_label.configure(
                    text=f"Não consegui ler '{os.path.basename(caminho)}': {erro}"
                )
                continue

            self._anexos_atuais.append({"nome": os.path.basename(caminho), "conteudo": conteudo})

        self._atualizar_indicador_anexo()

    def _remover_anexo(self, evento=None):
        self._anexos_atuais = []
        self._atualizar_indicador_anexo()

    def _atualizar_indicador_anexo(self):
        if self._anexos_atuais:
            nomes = ", ".join(anexo["nome"] for anexo in self._anexos_atuais)
            self.anexo_label.configure(text=f"📎 {nomes}   (clique para remover)")
            self.anexo_label.pack(fill="x", padx=10, pady=(0, 4), before=self.entrada_frame)
        else:
            self.anexo_label.pack_forget()

    # ---------- voz: push-to-talk (STT) e leitura das respostas (TTS) ----------

    def _iniciar_gravacao(self, evento=None):
        self._gravador.iniciar()
        self.status_label.configure(text="🎤 Gravando... solte o botão para transcrever")

    def _parar_gravacao(self, evento=None):
        caminho_audio = self._gravador.parar()
        if not caminho_audio:
            self.status_label.configure(text="")
            return

        self.status_label.configure(text="Transcrevendo áudio...")
        threading.Thread(target=self._transcrever_audio, args=(caminho_audio,), daemon=True).start()

    def _transcrever_audio(self, caminho_audio):
        texto = reconhecimento.transcrever(caminho_audio)
        self.after(0, self._preencher_transcricao, texto)

    def _preencher_transcricao(self, texto: str):
        self.status_label.configure(text="")
        if not texto:
            self.status_label.configure(text="Não entendi o áudio, tenta de novo.")
            return
        self.campo_mensagem.delete(0, "end")
        self.campo_mensagem.insert(0, texto)
        self.campo_mensagem.focus()

    def _alternar_voz(self):
        self._voz_ativa = not self._voz_ativa
        self.botao_voz.configure(text="🔊" if self._voz_ativa else "🔇")

    # ---------- barra lateral: lista de chats ----------

    def _atualizar_lista_chats(self):
        for widget in self._lista_chats_frame.winfo_children():
            widget.destroy()

        for chat_id in memoria.listar_chats():
            titulo = memoria.titulo_chat(chat_id)
            selecionado = chat_id == self.chat_atual

            item = tk.Label(
                self._lista_chats_frame,
                text=titulo,
                bg=COR_ITEM_SELECIONADO if selecionado else COR_SIDEBAR,
                fg="#ffffff" if selecionado else COR_TEXTO_SIDEBAR,
                anchor="w",
                justify="left",
                wraplength=190,
                padx=12,
                pady=8,
                cursor="hand2",
                font=FONTE,
            )
            item.pack(fill="x", padx=6, pady=2)
            item.bind("<Button-1>", lambda evento, id_escolhido=chat_id: self._trocar_chat(id_escolhido))
            item.bind("<Button-3>", lambda evento, id_escolhido=chat_id: self._menu_contexto_chat(evento, id_escolhido))
            self._vincular_rolagem(item, self._lista_canvas)

    def _menu_contexto_chat(self, evento, chat_id: str):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Renomear", command=lambda: self._renomear_chat(chat_id))
        menu.add_command(label="Apagar", command=lambda: self._apagar_chat(chat_id))
        menu.tk_popup(evento.x_root, evento.y_root)

    def _renomear_chat(self, chat_id: str):
        titulo_atual = memoria.titulo_chat(chat_id)
        novo_titulo = simpledialog.askstring(
            "Renomear chat", "Novo nome:", initialvalue=titulo_atual, parent=self
        )
        if novo_titulo and novo_titulo.strip():
            memoria.definir_titulo(chat_id, novo_titulo)
            self._atualizar_lista_chats()

    def _apagar_chat(self, chat_id: str):
        confirmar = messagebox.askyesno(
            "Apagar chat",
            f'Apagar a conversa "{memoria.titulo_chat(chat_id)}"? Essa ação não pode ser desfeita.',
            parent=self,
        )
        if not confirmar:
            return

        memoria.apagar_chat(chat_id)

        if chat_id == self.chat_atual:
            restantes = memoria.listar_chats()
            self.chat_atual = restantes[0] if restantes else memoria.novo_chat_id()
            self._limpar_mensagens()
            self._carregar_historico()

        self._atualizar_lista_chats()

    # ---------- troca e criação de chats ----------

    def _novo_chat(self):
        self.chat_atual = memoria.novo_chat_id()
        self._limpar_mensagens()
        self._atualizar_lista_chats()

    def _trocar_chat(self, chat_id: str):
        if chat_id == self.chat_atual:
            return
        self.chat_atual = chat_id
        self._limpar_mensagens()
        self._carregar_historico()
        self._atualizar_lista_chats()

    def _limpar_mensagens(self):
        for widget in self.mensagens_frame.winfo_children():
            widget.destroy()

    def _carregar_historico(self):
        for mensagem in memoria.carregar_historico(self.chat_atual):
            self._adicionar_mensagem(mensagem["remetente"], mensagem["texto"], salvar=False)

    # ---------- envio e resposta (com streaming) ----------

    def _enviar(self):
        texto = self.campo_mensagem.get().strip()
        if not texto and not self._anexos_atuais:
            return

        texto_exibido = texto
        texto_para_ia = texto

        if self._anexos_atuais:
            nomes = ", ".join(anexo["nome"] for anexo in self._anexos_atuais)
            texto_exibido = f"{texto}\n\n📎 {nomes}".strip()
            blocos = "\n\n".join(
                f'[Conteúdo do arquivo anexado "{anexo["nome"]}"]:\n{anexo["conteudo"]}'
                for anexo in self._anexos_atuais
            )
            texto_para_ia = f"{texto}\n\n{blocos}".strip()

        era_chat_novo = not memoria.carregar_historico(self.chat_atual)

        self._adicionar_mensagem("Você", texto_exibido)
        self.campo_mensagem.delete(0, "end")
        self._anexos_atuais = []
        self._atualizar_indicador_anexo()
        self._definir_processando(True)

        if era_chat_novo:
            self._atualizar_lista_chats()

        bolha_aria = self._criar_bolha_vazia("A.R.I.A.")
        threading.Thread(
            target=self._obter_resposta, args=(texto_para_ia, bolha_aria), daemon=True
        ).start()

    def _obter_resposta(self, texto, bolha_aria):
        acumulado = {"valor": ""}

        def ao_receber_pedaco(pedaco):
            acumulado["valor"] += pedaco
            self.after(0, self._definir_texto_bolha, bolha_aria, acumulado["valor"])

        resposta_final = ai_client.send_message(texto, ao_receber_pedaco)
        self.after(0, self._finalizar_resposta, bolha_aria, resposta_final)

    def _finalizar_resposta(self, bolha: tk.Text, texto_final: str):
        self._definir_processando(False)
        self._definir_texto_bolha(bolha, texto_final)
        memoria.salvar_mensagem(self.chat_atual, "A.R.I.A.", texto_final)

        if self._voz_ativa:
            threading.Thread(target=fala.falar, args=(texto_final,), daemon=True).start()

    # ---------- bolhas de mensagem (selecionáveis/copiáveis) ----------

    def _adicionar_mensagem(self, remetente: str, texto: str, salvar: bool = True):
        if salvar:
            memoria.salvar_mensagem(self.chat_atual, remetente, texto)
        bolha = self._criar_bolha_vazia(remetente)
        self._definir_texto_bolha(bolha, texto)

    def _criar_bolha_vazia(self, remetente: str) -> tk.Text:
        é_usuario = remetente == "Você"
        cor_bolha = COR_BOLHA_USUARIO if é_usuario else COR_BOLHA_ARIA
        cor_texto = COR_TEXTO_USUARIO if é_usuario else COR_TEXTO_ARIA
        lado = "e" if é_usuario else "w"

        linha = tk.Frame(self.mensagens_frame, bg=COR_FUNDO)
        linha.pack(fill="x", pady=4, padx=8)

        # Text em vez de Label: permite selecionar o texto e copiar (Ctrl+C),
        # mesmo estando "somente leitura" (state=disabled bloqueia edição,
        # não bloqueia seleção/cópia).
        bolha = tk.Text(
            linha,
            wrap="word",
            width=4,
            height=1,
            bg=cor_bolha,
            fg=cor_texto,
            insertbackground=cor_texto,
            selectbackground="#475569",
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            font=FONTE,
        )
        bolha.pack(anchor=lado)
        bolha.configure(state="disabled")
        bolha.tag_configure("negrito", font=(FONTE[0], FONTE[1], "bold"))

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        return bolha

    def _definir_texto_bolha(self, bolha: tk.Text, texto: str):
        bolha.configure(state="normal")
        bolha.delete("1.0", "end")

        # Suporte simples a markdown: só **negrito** por enquanto.
        partes = re.split(r"(\*\*.+?\*\*)", texto)
        for parte in partes:
            if parte.startswith("**") and parte.endswith("**") and len(parte) > 4:
                bolha.insert("end", parte[2:-2], "negrito")
            else:
                bolha.insert("end", parte)

        bolha.configure(state="disabled")

        texto_sem_marcacao = texto.replace("**", "")
        maior_linha = max((len(linha) for linha in texto_sem_marcacao.split("\n")), default=1)
        largura = max(4, min(maior_linha, LARGURA_MAX_BOLHA))
        bolha.configure(width=largura)

        bolha.update_idletasks()
        linhas = int(bolha.count("1.0", "end", "displaylines")[0])
        bolha.configure(height=max(linhas, 1))

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _definir_processando(self, processando: bool):
        self.status_label.configure(
            text="A.R.I.A. está digitando..." if processando else ""
        )
        self.botao_enviar.configure(state=tk.DISABLED if processando else tk.NORMAL)

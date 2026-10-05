"""
main.py — Ponto de entrada da A.R.I.A.

Só monta a interface e roda o loop principal do aplicativo.
"""

from ui import ChatApp


def main():
    app = ChatApp()
    app.mainloop()


if __name__ == "__main__":
    main()

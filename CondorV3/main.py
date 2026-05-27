import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from db.conexion import test_connection


def main():
    # Verificar conexión a PostgreSQL
    ok, err = test_connection()
    if not ok:
        sys.exit(1)

    root = tk.Tk()  #Sale la ventana
    from views.login_view import LoginWindow
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

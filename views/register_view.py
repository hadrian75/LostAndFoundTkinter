import tkinter as tk
from controllers.auth_controller import register_user

def open_register_window():
    win = tk.Toplevel()
    win.title("Register")

    tk.Label(win, text="Username").pack()
    username_entry = tk.Entry(win)
    username_entry.pack()

    tk.Label(win, text="Password").pack()
    password_entry = tk.Entry(win, show="*")
    password_entry.pack()

    def handle_register():
        username = username_entry.get()
        password = password_entry.get()
        if username and password:
            register_user(username, password)

    tk.Button(win, text="Register", command=handle_register).pack()

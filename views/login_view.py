import tkinter as tk
from controllers.auth_controller import login_user
from views.register_view import open_register_window

def open_login_window():
    win = tk.Tk()
    win.title("Login")

    tk.Label(win, text="Username").pack()
    username_entry = tk.Entry(win)
    username_entry.pack()

    tk.Label(win, text="Password").pack()
    password_entry = tk.Entry(win, show="*")
    password_entry.pack()

    def handle_login():
        username = username_entry.get()
        password = password_entry.get()
        if login_user(username, password):
            win.destroy()
            # lanjut ke dashboard (nanti bisa ditambahkan)
    
    tk.Button(win, text="Login", command=handle_login).pack()
    tk.Button(win, text="Register", command=open_register_window).pack()
    win.mainloop()
    

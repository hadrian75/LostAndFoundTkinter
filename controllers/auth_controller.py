import hashlib
from tkinter import messagebox
from db.connection import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE Username=%s AND PasswordHash=%s AND IsActive=1",
                       (username, hash_password(password)))
        user = cursor.fetchone()
        conn.close()

        if user:
            return True
        else:
            messagebox.showerror("Login Failed", "Username atau password salah!")
            return False
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return False

def register_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE Username=%s", (username,))
        if cursor.fetchone():
            messagebox.showerror("Register Failed", "Username sudah digunakan!")
            return

        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (CampusUserID, Username, PasswordHash) VALUES (%s, %s, %s)",
                       (1, username, password_hash))  # Dummy CampusUserID
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Registrasi berhasil!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

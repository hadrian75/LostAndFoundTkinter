# src/database/db_connector.py

import tkinter as tk # Import Tkinter
from tkinter import messagebox # Menggunakan messagebox untuk menampilkan error koneksi GUI
import mysql.connector
from dotenv import load_dotenv # Import load_dotenv untuk test block

load_dotenv()

from src.config import DB_CONFIG


def create_db_connection():
    """
    Membuat dan mengembalikan objek koneksi ke database MySQL.
    Menampilkan pesan error GUI jika koneksi gagal.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # print("Koneksi database berhasil!") # Opsional: untuk debugging
        return conn
    except mysql.connector.Error as err:
        # Menampilkan error koneksi di GUI menggunakan messagebox
        messagebox.showerror("Kesalahan Database", f"Gagal terhubung ke database:\n{err}")
        return None


def close_db_connection(conn):
    """
    Menutup objek koneksi database jika valid.
    """
    if conn and conn.is_connected():
        conn.close()
        # print("Koneksi database ditutup.") # Opsional: untuk debugging


# --- Test Block ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan db_connector.py langsung
    print("Testing database connection...")

    # Tkinter root window is needed for messagebox
    # Create a root window but hide it
    root = tk.Tk()
    root.withdraw()

    conn = create_db_connection()

    if conn:
        print("Database connection successful!")
        close_db_connection(conn)
    else:
        print("Database connection failed.")

    # Destroy the hidden root window
    root.destroy()

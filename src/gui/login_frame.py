# src/gui/login_frame.py

import tkinter as tk
from tkinter import messagebox
# Mengimpor BaseFrame dari paket gui (pastikan __init__.py ada di src/gui/)
from .base_frame import BaseFrame
# Mengimpor fungsi autentikasi dari DAO
from src.database.auth_dao import authenticate_user
# Mengimpor fungsi hashing password (masih dibutuhkan untuk registrasi, tapi tidak untuk login di sini)
# from src.utils.auth_utils import hash_password # TIDAK PERLU DIIMPOR UNTUK LOGIN

class LoginFrame(BaseFrame):
    """
    Frame untuk halaman Login.
    Mewarisi dari BaseFrame untuk fungsionalitas dasar.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi LoginFrame.

        Args:
            parent: Widget parent (biasanya jendela root).
            main_app: Referensi ke instance kelas MainApp (untuk navigasi).
        """
        super().__init__(parent, main_app)
        self.create_widgets() # Panggil metode untuk membuat widget

    def create_widgets(self):
        """Membuat widget (label, entry, tombol) untuk form login."""
        # Membersihkan widget lama jika metode ini dipanggil ulang (misal saat refresh frame)
        self.clear_widgets()

        tk.Label(self, text="Selamat Datang di CLFS", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text="Silakan Login ke Akun Anda", font=('Arial', 12)).pack(pady=(0, 20))

        # Frame terpisah untuk menampung input field agar layout lebih rapi
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Username:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_username = tk.Entry(input_frame, width=40)
        self.entry_username.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(input_frame, text="Password:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.entry_password = tk.Entry(input_frame, show="*", width=40) # show="*" untuk menyembunyikan input password
        self.entry_password.grid(row=1, column=1, pady=5, padx=5)

        # Tombol Login
        tk.Button(self, text="Login", command=self.handle_login, width=30).pack(pady=10)

        # Link ke halaman registrasi
        tk.Label(self, text="Belum punya akun?").pack(pady=(10, 0))
        # Menggunakan relief=tk.FLAT dan fg="blue" agar terlihat seperti hyperlink
        tk.Button(self, text="Daftar di sini", command=self.main_app.show_register_frame, relief=tk.FLAT, fg="blue", cursor="hand2").pack()

        # Link Lupa Password
        tk.Button(self, text="Lupa Password?", command=self.main_app.show_forgot_password_frame, relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(5, 0))


    def handle_login(self):
        """
        Menangani aksi saat tombol 'Login' diklik.
        Mengambil input, melakukan validasi, memanggil DAO untuk autentikasi.
        """
        username = self.entry_username.get().strip() # Ambil teks dari entry, hapus spasi di awal/akhir
        password = self.entry_password.get() # Ambil password ASLI

        # Validasi input kosong
        if not username or not password:
            messagebox.showwarning("Input Error", "Username dan password harus diisi.")
            return

        # Panggil fungsi autentikasi dari Data Access Object (DAO)
        # authenticate_user akan berinteraksi dengan tabel Users di database
        # KIRIM PASSWORD ASLI ke authenticate_user
        user_data = authenticate_user(username, password)

        if user_data:
            # Jika autentikasi berhasil (user_data tidak None)
            if user_data.get('IsActive'): # Pastikan akun pengguna aktif (email sudah diverifikasi)
                messagebox.showinfo("Sukses", f"Login berhasil! Selamat datang, {username}!")
                # Arahkan ke halaman utama aplikasi setelah login sukses
                self.main_app.show_main_app_frame(user_data) # Panggil metode di MainApp untuk ganti frame
            else:
                # Akun ditemukan tapi IsActive FALSE (belum verifikasi email)
                messagebox.showwarning("Login Gagal", "Akun Anda belum aktif. Mohon verifikasi email Anda.")
                # Arahkan pengguna ke halaman verifikasi OTP kembali
                # Anda perlu memastikan main_app memiliki metode show_otp_verification_frame
                # dan frame OTP dapat menerima user_id atau data lain untuk memuat ulang form verifikasi
                user_id = user_data.get('UserID')
                if user_id is not None:
                     # Panggil metode di MainApp untuk ganti frame ke OTP
                     # Pastikan MainApp.show_otp_verification_frame bisa menerima user_id
                     self.main_app.show_otp_verification_frame(user_id=user_id, username=username) # Contoh passing data
                else:
                     # Fallback jika somehow UserID tidak ada di user_data
                     messagebox.showerror("Error", "Tidak dapat mengarahkan ke halaman verifikasi. Silakan coba daftar ulang.")
                     self.main_app.show_register_frame() # Arahkan ke registrasi jika UserID tidak ditemukan
        else:
            # Jika autentikasi gagal (user_data adalah None)
            # Tampilkan pesan error umum di GUI
            messagebox.showwarning("Login Gagal", "Username atau password salah.")

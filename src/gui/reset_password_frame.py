# src/gui/reset_password_frame.py

import tkinter as tk
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi dari DAO untuk memproses reset password sebenarnya
from src.database.auth_dao import reset_password_with_token
# Mengimpor fungsi hashing password (diperlukan untuk menghash password baru sebelum dikirim ke DAO)
# from src.utils.auth_utils import hash_password # Hashing dilakukan di DAO sekarang

class ResetPasswordFrame(BaseFrame):
    """
    Frame untuk halaman Reset Password.
    Pengguna memasukkan token reset dan password baru mereka.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi ResetPasswordFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        # Variabel untuk menyimpan data token jika frame ini dibuka via link email (opsional)
        # self.token_data = None
        self.create_widgets() # Panggil metode untuk membuat widget

    def create_widgets(self):
        """Membuat widget untuk form reset password."""
        self.clear_widgets() # Bersihkan widget lama jika ada

        tk.Label(self, text="Reset Password", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text="Masukkan token reset dan password baru Anda.", font=('Arial', 12)).pack(pady=(0, 20))

        # Frame terpisah untuk menampung input field
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        # Label dan Entry untuk Token Reset
        tk.Label(input_frame, text="Token Reset:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_reset_token = tk.Entry(input_frame, width=40)
        self.entry_reset_token.grid(row=0, column=1, pady=5, padx=5)
        # Jika frame dibuka dengan token dari email, Anda bisa set nilai entry_reset_token di sini
        # if self.token_data:
        #     self.entry_reset_token.insert(0, self.token_data['token'])


        # Label dan Entry untuk Password Baru
        tk.Label(input_frame, text="Password Baru:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.entry_new_password = tk.Entry(input_frame, show="*", width=40)
        self.entry_new_password.grid(row=1, column=1, pady=5, padx=5)

        # Label dan Entry untuk Konfirmasi Password Baru
        tk.Label(input_frame, text="Konfirmasi Password:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.entry_confirm_password = tk.Entry(input_frame, show="*", width=40)
        self.entry_confirm_password.grid(row=2, column=1, pady=5, padx=5)

        # Tombol Reset Password
        tk.Button(self, text="Reset Password", command=self.handle_reset_password, width=30).pack(pady=10)

        # Link kembali ke login
        tk.Button(self, text="Kembali ke Login", command=self.main_app.show_login_frame, relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 0))

    # Metode opsional untuk menerima data token jika frame dibuka dari luar (misal dari link email)
    def set_token(self, token):
        """
        Mengatur nilai entry field token reset.
        Dipanggil oleh MainApp saat frame ini ditampilkan dengan token.
        """
        self.entry_reset_token.delete(0, tk.END) # Bersihkan field
        self.entry_reset_token.insert(0, token) # Isi dengan token yang diterima
        self.entry_new_password.focus_set() # Set fokus ke field password baru


    def handle_reset_password(self):
        """Menangani aksi saat tombol Reset Password diklik."""
        reset_token = self.entry_reset_token.get().strip()
        new_password = self.entry_new_password.get() # Ambil password baru (plain text)
        confirm_password = self.entry_confirm_password.get()

        if not all([reset_token, new_password, confirm_password]):
            messagebox.showwarning("Input Error", "Semua field harus diisi.")
            return

        if new_password != confirm_password:
            messagebox.showwarning("Input Error", "Password baru dan konfirmasi password tidak cocok.")
            return

        # TODO: Tambahkan validasi kekuatan password jika diperlukan (panjang min, karakter, dll.)
        # if len(new_password) < 8:
        #     messagebox.showwarning("Input Error", "Password minimal 8 karakter.")
        #     return

        # Panggil fungsi DAO untuk memproses reset password sebenarnya
        # Fungsi ini akan memverifikasi token dan mengupdate password.
        # Kita meneruskan token dan password baru (plain text) ke DAO.
        reset_success = reset_password_with_token(reset_token, new_password)

        if reset_success:
            messagebox.showinfo("Reset Berhasil", "Password Anda telah berhasil direset. Silakan login dengan password baru Anda.")
            # Arahkan kembali ke halaman login setelah reset berhasil
            self.main_app.show_login_frame()
        else:
            # Pesan error spesifik (token tidak valid, kedaluwarsa, sudah digunakan)
            # sudah ditangani dan ditampilkan oleh fungsi reset_password_with_token di auth_dao
            # Jika Anda ingin pesan error spesifik di GUI, Anda bisa memodifikasi
            # reset_password_with_token di DAO untuk mengembalikan kode error atau pesan.
            # Untuk saat ini, pesan error sudah muncul via print dari DAO.
            # Tampilkan pesan umum di GUI jika reset_password_with_token mengembalikan False
            messagebox.showwarning("Reset Gagal", "Gagal mereset password. Token tidak valid, sudah kedaluwarsa, atau sudah digunakan.")
            # Tetap di halaman reset password agar user bisa coba lagi atau periksa token

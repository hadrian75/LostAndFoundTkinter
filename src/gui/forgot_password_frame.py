# src/gui/forgot_password_frame.py

import tkinter as tk
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi dari DAO untuk request reset password
from src.database.auth_dao import request_password_reset
# Mengimpor fungsi untuk mengirim email
from src.utils.email_utils import send_email, get_reset_password_email_body # Mengimpor template body email reset password

class ForgotPasswordFrame(BaseFrame):
    """
    Frame untuk halaman Lupa Password.
    Pengguna memasukkan username atau email mereka untuk meminta reset password.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi ForgotPasswordFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.create_widgets() # Panggil metode untuk membuat widget

    def create_widgets(self):
        """Membuat widget untuk form lupa password."""
        self.clear_widgets() # Bersihkan widget lama jika ada

        tk.Label(self, text="Lupa Password?", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text="Masukkan Username atau Email terdaftar Anda.", font=('Arial', 12)).pack(pady=(0, 20))

        # Frame terpisah untuk menampung input field
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        # Label dan Entry untuk Username atau Email
        tk.Label(input_frame, text="Username atau Email:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_username_email = tk.Entry(input_frame, width=40)
        self.entry_username_email.grid(row=0, column=1, pady=5, padx=5)

        # Tombol Kirim Permintaan Reset
        tk.Button(self, text="Kirim Permintaan Reset", command=self.handle_request_reset, width=30).pack(pady=10)

        # Link kembali ke login
        tk.Button(self, text="Kembali ke Login", command=self.main_app.show_login_frame, relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 0))

    def handle_request_reset(self):
        """Menangani aksi saat tombol Kirim Permintaan Reset diklik."""
        username_or_email = self.entry_username_email.get().strip()

        if not username_or_email:
            messagebox.showwarning("Input Error", "Username atau Email harus diisi.")
            return

        # Panggil fungsi DAO untuk memproses permintaan reset password
        # Fungsi ini akan mencari user, membuat token, dan menyimpannya di DB.
        user_id, reset_token, user_email = request_password_reset(username_or_email)

        if user_id and reset_token and user_email:
            # Permintaan reset berhasil diproses di DB
            # Sekarang kirim email ke pengguna

            subject = "Instruksi Reset Password Akun CLFS Anda"
            # Gunakan template body email reset password yang baru
            # Pastikan get_reset_password_email_body menerima user_email atau user_full_name
            # Untuk demo, kita pakai email sebagai nama di template
            body = get_reset_password_email_body(user_email, reset_token, 30)


            # Kirim email (ini mungkin memakan waktu, pertimbangkan threading di aplikasi nyata)
            email_sent_success = send_email(user_email, subject, body)

            if email_sent_success:
                messagebox.showinfo("Permintaan Terkirim", f"Jika Username atau Email Anda terdaftar, instruksi reset password telah dikirim ke alamat email yang terkait dengan akun Anda ({user_email}). Silakan cek email Anda dan masukkan kode token di halaman Reset Password.")
                # Arahkan langsung ke halaman Reset Password dan isi tokennya
                self.main_app.show_reset_password_frame(reset_token) # Teruskan token ke MainApp
            else:
                # Email gagal dikirim - perlu penanganan lebih lanjut
                # Token sudah terbuat di DB, tapi email tidak sampai.
                messagebox.showwarning("Permintaan Diproses (Email Gagal)", f"Permintaan reset password Anda telah diproses, tetapi gagal mengirim instruksi ke email {user_email}. Mohon hubungi admin atau coba lagi nanti.")
                # Tetap di halaman lupa password atau kembali ke login
                # self.main_app.show_login_frame() # Kembali ke login

        else:
            # Pengguna tidak ditemukan atau error database saat request_password_reset
            # request_password_reset sudah menampilkan error database di konsol.
            # Penting: Jangan beritahu pengguna apakah username/email tidak ada di GUI untuk keamanan.
            # Beri pesan umum yang sama terlepas dari alasan kegagalan (user tidak ada atau DB error).
            messagebox.showinfo("Permintaan Diproses", "Jika Username atau Email Anda terdaftar, instruksi reset password telah dikirim ke alamat email yang terkait dengan akun Anda.")
            # Tetap di halaman lupa password atau kembali ke login
            # self.main_app.show_login_frame() # Kembali ke login


# TODO: Buat frame baru untuk memasukkan token dan password baru (ResetPasswordFrame)
# class ResetPasswordFrame(BaseFrame):
#     ... widget untuk input token, password baru, konfirmasi password ...
#     ... handle_reset_password method untuk memanggil DAO reset_password_with_token ...
#     pass

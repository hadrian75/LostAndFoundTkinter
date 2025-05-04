# src/gui/register_frame.py

import tkinter as tk
from tkinter import messagebox
# Mengimpor BaseFrame dari paket gui
from .base_frame import BaseFrame
# Mengimpor fungsi dari DAO untuk menyimpan user dan token
from src.database.auth_dao import create_new_user_with_token
# Mengimpor fungsi hashing password
from src.utils.auth_utils import hash_password
# Mengimpor fungsi untuk mengirim email dan template body email
from src.utils.email_utils import send_email, get_otp_email_body
import random # Untuk menghasilkan OTP
import datetime # Untuk mengelola waktu kedaluwarsa OTP

class RegisterFrame(BaseFrame):
    """
    Frame untuk halaman Registrasi.
    Mewarisi dari BaseFrame.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi RegisterFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.create_widgets() # Panggil metode untuk membuat widget

    def create_widgets(self):
        """Membuat widget untuk form registrasi."""
        self.clear_widgets() # Bersihkan widget lama jika ada

        tk.Label(self, text="Daftar Akun Baru", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text="Isi data diri Anda", font=('Arial', 12)).pack(pady=(0, 20))

        # Frame untuk input menggunakan grid untuk layout yang lebih terstruktur
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        # Label dan Entry untuk Nama Lengkap
        tk.Label(input_frame, text="Nama Lengkap:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_full_name = tk.Entry(input_frame, width=40)
        self.entry_full_name.grid(row=0, column=1, pady=5, padx=5)

        # Label dan Entry untuk NIM/NIP
        tk.Label(input_frame, text="NIM/NIP:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.entry_nim_nip = tk.Entry(input_frame, width=40)
        self.entry_nim_nip.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(input_frame, text="Email Kampus:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.entry_email = tk.Entry(input_frame, width=40)
        self.entry_email.grid(row=2, column=1, pady=5, padx=5)

        # Label dan Entry untuk Role ID (idealnya pakai OptionMenu/ComboBox)
        tk.Label(input_frame, text="Role ID (1=Mhs, 2=Admin, 3=Staf):").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.entry_role_id = tk.Entry(input_frame, width=40)
        self.entry_role_id.grid(row=3, column=1, pady=5, padx=5)

        # Label dan Entry untuk Username
        tk.Label(input_frame, text="Username:").grid(row=4, column=0, sticky='w', pady=5, padx=5)
        self.entry_username = tk.Entry(input_frame, width=40)
        self.entry_username.grid(row=4, column=1, pady=5, padx=5)

        # Label dan Entry untuk Password
        tk.Label(input_frame, text="Password:").grid(row=5, column=0, sticky='w', pady=5, padx=5)
        self.entry_password = tk.Entry(input_frame, show="*", width=40)
        self.entry_password.grid(row=5, column=1, pady=5, padx=5)

        # Tombol Daftar
        tk.Button(self, text="Daftar", command=self.handle_register, width=30).pack(pady=10)

        # Link kembali ke login
        tk.Label(self, text="Sudah punya akun?").pack(pady=(10, 0))
        tk.Button(self, text="Login di sini", command=self.main_app.show_login_frame, relief=tk.FLAT, fg="blue", cursor="hand2").pack()

    def handle_register(self):
        """
        Menangani aksi saat tombol 'Daftar' diklik.
        Mengambil input, validasi, menghasilkan OTP, menyimpan ke DB, dan mengirim email.
        """
        # Ambil data dari entry field dan hapus spasi di awal/akhir (kecuali password)
        full_name = self.entry_full_name.get().strip()
        nim_nip = self.entry_nim_nip.get().strip()
        email = self.entry_email.get().strip()
        role_id_str = self.entry_role_id.get().strip()
        username = self.entry_username.get().strip()
        password = self.entry_password.get() # Password tidak perlu strip trailing/leading whitespace

        # Validasi input kosong
        if not all([full_name, nim_nip, email, role_id_str, username, password]):
            messagebox.showwarning("Input Error", "Semua field harus diisi.")
            return

        # Validasi Role ID (konversi ke integer)
        try:
            role_id = int(role_id_str)
            # TODO: Validasi RoleID lebih lanjut, misalnya cek apakah RoleID ada di tabel Roles
            if role_id not in [1, 2, 3]: # Contoh validasi dasar sesuai data dummy
                 messagebox.showwarning("Input Error", "Role ID tidak valid. Gunakan 1, 2, atau 3.")
                 return
        except ValueError:
            messagebox.showwarning("Input Error", "Role ID harus berupa angka.")
            return

        # Hash password menggunakan fungsi dari auth_utils
        password_hash = hash_password(password)

        # Hasilkan OTP (6 digit angka acak) dan hitung waktu kedaluwarsa
        otp_code = str(random.randint(100000, 999999))
        # Mengambil durasi kedaluwarsa dari instance MainApp
        otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=self.main_app.otp_expiry_minutes)

        # Panggil fungsi DAO untuk menyimpan data pengguna baru dan token verifikasi
        # Fungsi ini akan melakukan INSERT ke tabel CampusUsers, Users, dan EmailVerificationToken
        user_id = create_new_user_with_token(full_name, nim_nip, email, role_id, username, password_hash, otp_code, otp_expiry)

        if user_id:
            # Jika data user dan token berhasil disimpan di database (user_id tidak None)

            # Siapkan subjek dan isi email menggunakan template
            subject = "Kode Aktivasi Akun CLFS Kamu nih! ✨"
            body = get_otp_email_body(full_name, otp_code, self.main_app.otp_expiry_minutes)

            # Kirim email (ini mungkin memakan waktu, pertimbangkan threading di aplikasi nyata)
            email_sent_success = send_email(email, subject, body)

            if email_sent_success:
                messagebox.showinfo("Registrasi Berhasil", f"Akun berhasil dibuat! Kode verifikasi telah dikirim ke email {email}. Silakan cek email Anda dan masukkan kode di halaman berikutnya.")
                # Arahkan pengguna ke halaman verifikasi OTP, teruskan UserID yang baru dibuat
                self.main_app.show_otp_verification_frame(user_id)
            else:
                # Email gagal dikirim - perlu penanganan lebih lanjut
                # Misalnya, beri tahu pengguna untuk menghubungi admin atau coba lagi
                messagebox.showwarning("Registrasi Berhasil (Email Gagal)", f"Akun berhasil dibuat, tetapi gagal mengirim kode verifikasi ke email {email}. Mohon periksa folder spam Anda atau hubungi admin jika masalah berlanjut.")
                # Tetap arahkan ke halaman OTP jika user bisa memasukkan kode secara manual (misal dari log admin)
                self.main_app.show_otp_verification_frame(user_id) # Tetap coba arahkan ke OTP

        # Jika create_new_user_with_token mengembalikan None, error sudah ditangani di DAO
        # (misal: username/email/nim_nip duplikat) dan pesan error sudah ditampilkan oleh DAO.

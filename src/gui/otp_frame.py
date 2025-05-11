# src/gui/otp_frame.py

import tkinter as tk
from tkinter import messagebox
# Mengimpor BaseFrame dari paket gui
from .base_frame import BaseFrame
# Mengimpor fungsi verifikasi token dan fungsi hapus user dari DAO
from src.database.auth_dao import verify_email_token, delete_user_and_campus_user_by_id # Import fungsi delete

class OTPFrame(BaseFrame):
    """
    Frame untuk halaman Verifikasi OTP.
    Mewarisi dari BaseFrame.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi OTPFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        # Variabel untuk menyimpan UserID pengguna yang sedang diverifikasi
        self.user_id_to_verify = None
        # Variabel untuk menyimpan username (opsional, bisa berguna untuk pesan)
        self.username_to_verify = None
        self.create_widgets() # Panggil metode untuk membuat widget

    def create_widgets(self):
        """Membuat widget untuk form verifikasi OTP."""
        self.clear_widgets() # Bersihkan widget lama jika ada

        tk.Label(self, text="Verifikasi Email Anda", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text="Masukkan kode OTP yang dikirim ke email Anda.", font=('Arial', 12)).pack(pady=(0, 20))

        # Frame untuk input OTP
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        # Label dan Entry untuk Kode OTP
        tk.Label(input_frame, text="Kode OTP:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_otp = tk.Entry(input_frame, width=40)
        self.entry_otp.grid(row=0, column=1, pady=5, padx=5)

        # Tombol Verifikasi
        tk.Button(self, text="Verifikasi", command=self.handle_verification, width=30).pack(pady=10)

        # (Opsional) Tombol Kirim Ulang OTP - perlu implementasi logika di sini
        # tk.Button(self, text="Kirim Ulang OTP", command=self.handle_resend_otp, relief=tk.FLAT, fg="blue", cursor="hand2").pack()

        # Link kembali ke login (jika pengguna ingin membatalkan atau sudah verifikasi sebelumnya)
        # Ubah command untuk memanggil handler baru
        tk.Label(self, text="Sudah verifikasi atau ingin batal?").pack(pady=(10, 0))
        tk.Button(
            self,
            text="Kembali ke Login",
            command=self.handle_cancel_verification, # <-- Panggil handler baru di sini
            relief=tk.FLAT,
            fg="blue",
            cursor="hand2"
        ).pack()

    def set_user_to_verify(self, user_id, username=None):
        """
        Metode yang dipanggil oleh MainApp untuk mengatur UserID (dan opsional username)
        pengguna yang perlu diverifikasi di frame ini.
        """
        self.user_id_to_verify = user_id
        self.username_to_verify = username
        # Opsional: Tampilkan pesan ke user tentang email mana OTP dikirim
        # Untuk ini, Anda perlu meneruskan email pengguna juga dari RegisterFrame ke MainApp, lalu ke sini.
        # Misalnya, tambahkan label di create_widgets dan update teksnya di sini.
        # if username:
        #     print(f"Verifying user: {username} (ID: {user_id})") # Debugging print


    def handle_verification(self):
        """
        Menangani aksi saat tombol 'Verifikasi' diklik.
        Mengambil input OTP dan memanggil DAO untuk verifikasi.
        """
        otp_code = self.entry_otp.get().strip()

        # Validasi input kosong
        if not otp_code:
            messagebox.showwarning("Input Error", "Kode OTP harus diisi.")
            return

        # Periksa apakah UserID yang perlu diverifikasi sudah diatur
        if self.user_id_to_verify is None:
            messagebox.showerror("Kesalahan", "Tidak ada pengguna yang perlu diverifikasi. Silakan coba daftar ulang atau login.")
            self.main_app.show_login_frame() # Arahkan kembali ke login
            return

        # Panggil fungsi DAO untuk memverifikasi token
        # Fungsi verify_email_token akan menangani validasi token, kedaluwarsa, dan status IsUsed
        verification_success = verify_email_token(self.user_id_to_verify, otp_code)

        if verification_success:
            # Jika verifikasi berhasil (akun IsActive diubah menjadi TRUE di DB)
            messagebox.showinfo("Sukses", "Verifikasi email berhasil! Akun Anda sekarang aktif. Silakan login.")
            self.user_id_to_verify = None # Reset UserID setelah sukses verifikasi
            self.username_to_verify = None
            self.main_app.show_login_frame() # Arahkan pengguna ke halaman login
        else:
            # Jika verifikasi gagal (token salah, kedaluwarsa, sudah digunakan, dll.)
            messagebox.showwarning("Verifikasi Gagal", "Kode OTP tidak valid, sudah kedaluwarsa, atau sudah digunakan.")
            # Tetap di halaman OTP agar user bisa coba lagi atau minta kirim ulang
            # entry_otp.delete(0, tk.END) # Opsional: Bersihkan field OTP setelah gagal

    def handle_cancel_verification(self):
        """
        Menangani aksi saat tombol 'Kembali ke Login' diklik.
        Menghapus akun pengguna yang belum aktif dan mengarahkan ke halaman login.
        """
        print(f"Attempting to cancel verification for UserID: {self.user_id_to_verify}") # Debugging print
        if self.user_id_to_verify is not None:
            # Konfirmasi ke pengguna sebelum menghapus akun
            confirm = messagebox.askyesno(
                "Konfirmasi Pembatalan",
                "Anda belum menyelesaikan verifikasi email. Jika Anda kembali ke halaman login sekarang, akun Anda akan dihapus. Lanjutkan?"
            )
            if confirm:
                # Panggil fungsi DAO untuk menghapus pengguna dan campus user
                success = delete_user_and_campus_user_by_id(self.user_id_to_verify)

                if success:
                    messagebox.showinfo("Pembatalan Berhasil", "Akun Anda telah dihapus.")
                else:
                    # Jika penghapusan gagal di DB, beri tahu pengguna tapi tetap lanjutkan ke login
                    # agar tidak terjebak di halaman ini.
                    messagebox.showwarning("Info", "Tidak dapat menghapus akun, namun Anda dapat mendaftar ulang.") # Opsional

                self.user_id_to_verify = None # Reset UserID setelah mencoba hapus
                self.username_to_verify = None
                self.main_app.show_login_frame() # Arahkan kembali ke login
            else:
                 # Jika pengguna membatalkan konfirmasi, tetap di halaman OTP
                 pass # Do nothing, stay on current frame
        else:
            # Jika user_id_to_verify tidak diset (misal, pengguna langsung ke halaman ini tanpa registrasi/login tidak aktif)
            # Langsung arahkan ke login tanpa mencoba menghapus
            print("No user_id_to_verify set, redirecting directly to login.") # Debugging print
            self.main_app.show_login_frame()


    # Tambahkan atau pastikan metode show() ada jika BaseFrame tidak menyediakannya
    # def show(self):
    #     super().show()
    #     # Logika tambahan saat frame ditampilkan, misal:
    #     # self.create_widgets() # Jika widget perlu dibuat ulang setiap kali show
    #     # Jika set_user_to_verify dipanggil sebelum show, tidak perlu argumen di sini
    #     # Jika set_user_to_verify dipanggil setelah show, MainApp perlu memanggilnya secara eksplisit.
    #     pass

    # Tambahkan atau pastikan metode hide() ada jika BaseFrame tidak menyediakannya
    # def hide(self):
    #     super().hide()
    #     # Logika tambahan saat frame disembunyikan
    #     # Misalnya, membersihkan field input:
    #     # self.entry_otp.delete(0, tk.END)
    #     pass

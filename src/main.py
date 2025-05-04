# src/main.py

import tkinter as tk
from dotenv import load_dotenv # Untuk memuat variabel lingkungan
import os # Untuk mengakses variabel lingkungan
from tkinter import messagebox # Import messagebox

# Memuat variabel lingkungan dari file .env di awal aplikasi
# Pastikan file .env ada di direktori akar proyek
load_dotenv()

# Mengimpor frame-frame GUI dari paket src.gui
# Pastikan __init__.py ada di src/gui/
from src.gui.login_frame import LoginFrame
from src.gui.register_frame import RegisterFrame
from src.gui.otp_frame import OTPFrame
from src.gui.main_app_frame import MainAppFrame
from src.gui.forgot_password_frame import ForgotPasswordFrame
from src.gui.reset_password_frame import ResetPasswordFrame # Impor ResetPasswordFrame yang baru

# Mengakses konfigurasi lain dari .env jika diperlukan
# Misalnya, durasi kedaluwarsa OTP dari .env
# Menggunakan .get() dengan default value untuk menghindari error jika variabel tidak ada di .env
OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', '15')) # Default 15 menit, pastikan default adalah string jika menggunakan int()

class MainApp:
    """
    Kelas utama aplikasi yang mengelola jendela root Tkinter dan perpindahan antar frame.
    Ini adalah controller utama GUI.
    """
    def __init__(self, root):
        """
        Inisialisasi MainApp.

        Args:
            root: Jendela root Tkinter (objek tk.Tk()).
        """
        self.root = root
        self.root.title("Campus Lost and Found System (CLFS)")
        self.root.geometry("800x600") # Ukuran jendela default (lebar x tinggi) - Disesuaikan
        self.root.resizable(True, True) # Aktifkan resize jendela (opsional, disarankan untuk main frame)


        # Menyimpan durasi kedaluwarsa OTP agar bisa diakses oleh frame lain jika diperlukan
        self.otp_expiry_minutes = OTP_EXPIRY_MINUTES

        # Membuat instance dari setiap frame GUI
        # Semua frame dibuat di awal, dan hanya satu yang ditampilkan pada satu waktu
        # Meneruskan 'self' (instance MainApp) ke setiap frame agar mereka bisa memanggil metode show_frame di MainApp
        self.login_frame = LoginFrame(self.root, self)
        self.register_frame = RegisterFrame(self.root, self)
        self.otp_frame = OTPFrame(self.root, self)
        self.main_app_frame = MainAppFrame(self.root, self)
        self.forgot_password_frame = ForgotPasswordFrame(self.root, self)
        self.reset_password_frame = ResetPasswordFrame(self.root, self) # Buat instance ResetPasswordFrame


        # Tampilkan frame pertama saat aplikasi dimulai (Login)
        self.show_login_frame()

    def show_frame(self, frame_to_show):
        """
        Menyembunyikan semua frame yang mungkin sedang ditampilkan
        dan menampilkan frame yang diminta.

        Args:
            frame_to_show: Instance frame (objek yang mewarisi dari BaseFrame) yang ingin ditampilkan.
        """
        # Sembunyikan semua frame yang mungkin sedang ditampilkan
        # Menggunakan try-except untuk berjaga-jaga jika instance frame belum dibuat atau None
        try:
            self.login_frame.hide()
        except AttributeError: pass
        try:
            self.register_frame.hide()
        except AttributeError: pass
        try:
            self.otp_frame.hide()
        except AttributeError: pass
        try:
            self.main_app_frame.hide()
        except AttributeError: pass
        try:
            self.forgot_password_frame.hide()
        except AttributeError: pass
        try:
            self.reset_password_frame.hide() # Sembunyikan ResetPasswordFrame
        except AttributeError: pass


        # Tampilkan frame yang diminta
        frame_to_show.show()

    def show_login_frame(self):
        """Menampilkan frame Login."""
        self.show_frame(self.login_frame)
        # Set fokus ke entry field pertama di frame login untuk kemudahan pengguna
        self.login_frame.entry_username.focus_set()

    def show_register_frame(self):
        """Menampilkan frame Registrasi."""
        self.show_frame(self.register_frame)
        # Set fokus ke entry field pertama di frame register
        self.register_frame.entry_full_name.focus_set()

    def show_otp_verification_frame(self, user_id):
        """
        Menampilkan frame Verifikasi OTP dan mengatur UserID pengguna
        yang baru mendaftar untuk diverifikasi.

        Args:
            user_id (int): UserID dari pengguna yang baru mendaftar (didapat dari DAO).
        """
        # Mengatur UserID di frame OTP agar frame tersebut tahu pengguna mana yang perlu diverifikasi
        self.otp_frame.set_user_to_verify(user_id)
        self.show_frame(self.otp_frame)
        # Set fokus ke entry field OTP
        self.otp_frame.entry_otp.focus_set()

    def show_main_app_frame(self, user_data):
        """
        Menampilkan frame utama aplikasi setelah login berhasil.
        Menerima data pengguna yang login untuk diproses di frame utama.

        Args:
            user_data (dict): Dictionary berisi data pengguna yang login (UserID, IsActive, IsAdmin).
                              Anda mungkin ingin menambahkan FullName, RoleName, NIM_NIP, Email di sini
                              dengan memanggil DAO lain jika diperlukan.
        """
        print(f"Login Sukses! Menampilkan halaman utama untuk UserID: {user_data['UserID']}, IsAdmin: {user_data['IsAdmin']}")

        # TODO: Ambil data CampusUser (FullName, NIM_NIP, Email, RoleName) berdasarkan UserID
        # Anda perlu membuat fungsi di user_dao.py untuk ini
        # from src.database.user_dao import get_campus_user_details_by_user_id
        # campus_user_details = get_campus_user_details_by_user_id(user_data['UserID'])
        # if campus_user_details:
        #    user_data.update(campus_user_details) # Tambahkan detail campus user ke user_data

        # Mengatur data pengguna di MainAppFrame
        self.main_app_frame.set_user_data(user_data)

        # Menampilkan MainAppFrame
        self.show_frame(self.main_app_frame)

    def show_forgot_password_frame(self):
        """Menampilkan frame Lupa Password."""
        self.show_frame(self.forgot_password_frame)
        self.forgot_password_frame.entry_username_email.focus_set() # Set fokus ke field input

    def show_reset_password_frame(self, reset_token=None):
        """
        Menampilkan frame Reset Password.
        Opsional menerima token reset untuk mengisi field secara otomatis.

        Args:
            reset_token (str, optional): Token reset password jika tersedia.
        """
        # Anda bisa meneruskan token ke frame reset password jika frame tersebut memiliki metode untuk menerimanya
        # self.reset_password_frame.set_token(reset_token) # Perlu implementasi di ResetPasswordFrame
        self.show_frame(self.reset_password_frame)
        # Set fokus ke field token atau password baru
        if reset_token:
             # Jika token diberikan, set fokus ke password baru
             # self.reset_password_frame.entry_new_password.focus_set()
             # Dan isi field token
             # self.reset_password_frame.entry_reset_token.delete(0, tk.END)
             # self.reset_password_frame.entry_reset_token.insert(0, reset_token)
             pass # Implementasi set token di ResetPasswordFrame diperlukan
        else:
             # Jika token tidak diberikan (misal, navigasi manual), set fokus ke field token
             self.reset_password_frame.entry_reset_token.focus_set()


# --- Jalankan Aplikasi ---
if __name__ == "__main__":
    # Membuat jendela root Tkinter
    root = tk.Tk()
    # Membuat instance kelas MainApp, memulai aplikasi
    app = MainApp(root)
    # Memulai event loop Tkinter
    root.mainloop()

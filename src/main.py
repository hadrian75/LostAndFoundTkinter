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
from src.gui.reset_password_frame import ResetPasswordFrame
from src.gui.report_item_frame import ReportItemFrame
from src.gui.view_items_frame import ViewItemsFrame
from src.gui.claim_item_frame import ClaimItemFrame
from src.gui.my_claims_frame import MyClaimsFrame
from src.gui.admin_panel_frame import AdminPanelFrame
from src.gui.notifications_frame import NotificationsFrame # Impor NotificationsFrame yang baru
from src.gui.user_profile_frame import UserProfileFrame
from src.gui.admin_panel_user_frame import AdminPanelUserFrame



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

        # --- Atribut untuk menyimpan data pengguna yang sedang login ---
        self.user_data = None # Akan menyimpan dictionary data pengguna setelah login berhasil


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
        self.reset_password_frame = ResetPasswordFrame(self.root, self)
        self.report_item_frame = ReportItemFrame(self.root, self)
        self.view_items_frame = ViewItemsFrame(self.root, self)
        self.claim_item_frame = ClaimItemFrame(self.root, self)
        self.my_claims_frame = MyClaimsFrame(self.root, self)
        self.admin_panel_frame = AdminPanelFrame(self.root, self)
        self.notifications_frame = NotificationsFrame(self.root, self) 
        self.user_profile_frame = UserProfileFrame(self.root, self) 
        self.admin_panel_user_frame = AdminPanelUserFrame(self.root, self)


        # Buat instance frame lain di sini


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
            self.reset_password_frame.hide()
        except AttributeError: pass
        try:
            self.report_item_frame.hide()
        except AttributeError: pass
        try:
            self.view_items_frame.hide()
        except AttributeError: pass
        try:
            self.claim_item_frame.hide()
        except AttributeError: pass
        try:
            self.my_claims_frame.hide()
        except AttributeError: pass
        try:
            self.admin_panel_frame.hide()
        except AttributeError: pass
        try:
            self.notifications_frame.hide() # Pastikan notifications_frame disembunyikan
        except AttributeError: pass
        try:
            self.user_profile_frame.hide()
        except AttributeError: pass
        try:
            self.admin_panel_user_frame.hide()
        except AttributeError: pass
        # Sembunyikan frame lain di sini


        # Tampilkan frame yang diminta
        frame_to_show.show()
    def show_user_profile_frame(self):
        """Show the user profile editing frame"""
        if self.user_data:
            self.user_profile_frame.set_user_id(self.user_data['UserID'])
            self.show_frame(self.user_profile_frame)
        else:
            messagebox.showerror("Error", "No user data available")
    def show_login_frame(self):
        """Menampilkan frame Login."""
        # Reset user_data saat kembali ke login
        self.user_data = None
        self.show_frame(self.login_frame)
        # Set fokus ke entry field pertama di frame login untuk kemudahan pengguna
        self.login_frame.entry_username.focus_set()

    def show_register_frame(self):
        """Menampilkan frame Registrasi."""
        self.show_frame(self.register_frame)
        # Set fokus ke entry field pertama di frame register
        self.register_frame.entry_full_name.focus_set()

    def show_otp_verification_frame(self, user_id, username=None): # Tambahkan parameter username
        """
        Menampilkan frame Verifikasi OTP dan mengatur UserID (dan opsional username)
        pengguna yang baru mendaftar atau login dengan akun tidak aktif untuk diverifikasi.

        Args:
            user_id (int): UserID dari pengguna.
            username (str, optional): Username pengguna. Default None.
        """
        print(f"MainApp: show_otp_verification_frame called for UserID: {user_id}, Username: {username}") # Debugging print
        # Mengatur UserID (dan username) di frame OTP
        self.otp_frame.set_user_to_verify(user_id, username) # Teruskan username juga
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
        print(f"MainApp: show_main_app_frame called for UserID: {user_data['UserID']}, IsAdmin: {user_data['IsAdmin']}")

        # --- Simpan user_data di instance MainApp ---
        self.user_data = user_data



        # Menampilkan MainAppFrame
        self.show_frame(self.main_app_frame)

    def show_forgot_password_frame(self):
        """Menampilkan frame Lupa Password."""
        print("MainApp: show_forgot_password_frame called.") # Debugging print
        self.show_frame(self.forgot_password_frame)
        self.forgot_password_frame.entry_username_email.focus_set() # Set fokus ke field input

    def show_reset_password_frame(self, reset_token=None):
        """
        Menampilkan frame Reset Password.
        Opsional menerima token reset untuk mengisi field secara otomatis.

        Args:
            reset_token (str, optional): Token reset password jika tersedia.
        """
        print(f"MainApp: show_reset_password_frame called with token: {reset_token}") # Debugging print
        # Meneruskan token ke frame reset password jika frame tersebut memiliki metode set_token
        if reset_token and hasattr(self.reset_password_frame, 'set_token'):
             print(f"MainApp: Calling set_token({reset_token}) on ResetPasswordFrame.") # Debugging print
             self.reset_password_frame.set_token(reset_token) # Perlu implementasi di ResetPasswordFrame
        else:
             print("MainApp: show_reset_password_frame called without token or ResetPasswordFrame has no set_token method.") # Debugging print


        self.show_frame(self.reset_password_frame)
        # Set fokus ke field token atau password baru di ResetPasswordFrame
        # Fokus akan diatur di set_token() jika token ada, atau di create_widgets() jika tidak
        # Jadi tidak perlu set fokus di sini

    def show_report_item_frame(self):
        """Menampilkan frame Laporkan Barang Ditemukan."""
        print("MainApp: show_report_item_frame called.") # Debugging print
        self.show_frame(self.report_item_frame)
        self.report_item_frame.entry_item_name.focus_set() # Set fokus ke field pertama di form

    def show_view_items_frame(self):
        """Menampilkan frame Daftar Barang Ditemukan."""
        print("MainApp: show_view_items_frame called.") # Debugging print
        # load_items dan display_items dipanggil di metode show() di ViewItemsFrame
        self.show_frame(self.view_items_frame)

    def show_claim_item_frame(self, item_id):
        """
        Menampilkan frame Ajukan Klaim Barang untuk item tertentu.

        Args:
            item_id (int): ItemID dari barang yang akan diklaim.
        """
        print(f"MainApp: show_claim_item_frame called for ItemID: {item_id}") # DEBUGGING PRINT
        # Set ItemID di ClaimItemFrame agar frame tersebut tahu barang mana yang diklaim
        if hasattr(self.claim_item_frame, 'set_item_id'):
             print(f"MainApp: Calling set_item_id({item_id}) on ClaimItemFrame.") # DEBUGGING PRINT
             self.claim_item_frame.set_item_id(item_id)
        else:
             print("MainApp: ClaimItemFrame does not have set_item_id method.") # DEBUGGING PRINT

        self.show_frame(self.claim_item_frame)

    def show_my_claims_frame(self):
        """
        Menampilkan frame Daftar Klaim Saya.
        """
        print("MainApp: show_my_claims_frame called.") # Debugging print
        # load_claims_data dan display_claims dipanggil di metode show() di MyClaimsFrame
        self.show_frame(self.my_claims_frame)

    def show_admin_panel_frame(self):
        """
        Menampilkan frame Panel Admin.
        """
        print("MainApp: show_admin_panel_frame called.") # Debugging print
        # load_pending_claims dan display_claims dipanggil di metode show() di AdminPanelFrame
        self.show_frame(self.admin_panel_frame)

    # --- metode buat show frame nofiikasi ---
    def show_notifications_frame(self):
        """
        Menampilkan frame Notifikasi Pengguna.
        """
        print("MainApp: show_notifications_frame called.") # Debugging print
        self.show_frame(self.notifications_frame)
    def show_admin_panel_user(self):
        """Show admin user management panel"""
        if not self.user_data or not self.user_data.get('IsAdmin'):
            messagebox.showwarning("Access Denied", "Only administrators can access this feature")
            return
        
        self.show_frame(self.admin_panel_user_frame)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.geometry("1600x2400")
    app = MainApp(root)
    root.mainloop()

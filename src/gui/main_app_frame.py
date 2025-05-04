# src/gui/main_app_frame.py

import tkinter as tk
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame dari paket gui
# Anda mungkin perlu mengimpor DAO lain di sini nanti (misal: item_dao, claim_dao)
# from src.database.item_dao import get_all_items
# from src.database.claim_dao import get_claims_by_user

class MainAppFrame(BaseFrame):
    """
    Frame untuk halaman utama aplikasi setelah login berhasil.
    Akan menampilkan konten berbeda tergantung peran pengguna.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi MainAppFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.user_data = None # Untuk menyimpan data pengguna yang sedang login

    def set_user_data(self, user_data):
        """
        Mengatur data pengguna yang sedang login dan memperbarui tampilan frame.

        Args:
            user_data (dict): Dictionary berisi data pengguna yang login (UserID, IsActive, IsAdmin).
                              Anda mungkin ingin mengambil data CampusUser (FullName, RoleID, NIM_NIP, Email)
                              di sini atau di LoginFrame dan meneruskannya.
        """
        self.user_data = user_data
        print(f"MainAppFrame received user data: {self.user_data}") # Debugging print
        self.create_widgets() # Panggil ulang create_widgets untuk memperbarui UI berdasarkan user_data

    def create_widgets(self):
        """
        Membuat widget untuk halaman utama.
        Layout dan konten bisa berbeda berdasarkan self.user_data (terutama IsAdmin).
        """
        self.clear_widgets() # Bersihkan widget lama

        if self.user_data is None:
            # Tampilkan pesan error atau kembali ke login jika data user tidak ada
            tk.Label(self, text="Error: User data not loaded.", fg="red").pack(pady=20)
            tk.Button(self, text="Kembali ke Login", command=self.main_app.show_login_frame).pack(pady=10)
            return

        # --- Bagian Header/Selamat Datang ---
        # Anda perlu mengambil FullName dari CampusUsers berdasarkan UserID
        # Untuk demo, kita pakai Username dulu atau tambahkan logika ambil FullName
        # Asumsi user_data sekarang juga menyertakan FullName (Anda bisa tambahkan ini di authenticate_user DAO)
        # Atau ambil FullName di sini:
        # full_name = get_full_name_by_user_id(self.user_data['UserID']) # Perlu fungsi DAO baru

        # Untuk demo, gunakan Username atau tambahkan FullName ke user_data di MainApp
        username = self.user_data.get('Username', 'Pengguna') # Ambil Username jika ada, default 'Pengguna'
        # Jika Anda sudah memodifikasi authenticate_user untuk mengembalikan FullName:
        # full_name = self.user_data.get('FullName', username)

        tk.Label(self, text=f"Selamat Datang, {username}!", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text=f"Role: {'Admin' if self.user_data.get('IsAdmin') else 'Pengguna Biasa'}").pack(pady=(0, 20))
        # Anda bisa tampilkan NIM/NIP, Email, dll di sini

        # --- Bagian Konten Utama (Bisa Berbeda untuk Admin) ---

        if self.user_data.get('IsAdmin'):
            # --- Tampilan untuk Admin ---
            tk.Label(self, text="Panel Admin", font=('Arial', 16)).pack(pady=10)
            tk.Button(self, text="Kelola Barang Hilang/Ditemukan", command=self.show_manage_items).pack(pady=5)
            tk.Button(self, text="Verifikasi Klaim", command=self.show_verify_claims).pack(pady=5)
            tk.Button(self, text="Kelola Pengguna", command=self.show_manage_users).pack(pady=5)
            # Tambahkan tombol/opsi khusus admin lainnya

        else:
            # --- Tampilan untuk Pengguna Biasa (Student/Staff) ---
            tk.Label(self, text="Menu Pengguna", font=('Arial', 16)).pack(pady=10)
            tk.Button(self, text="Lihat Barang Ditemukan", command=self.show_view_found_items).pack(pady=5)
            tk.Button(self, text="Laporkan Barang Ditemukan", command=self.show_report_item).pack(pady=5)
            tk.Button(self, text="Lihat Klaim Saya", command=self.show_my_claims).pack(pady=5)
            tk.Button(self, text="Lihat Notifikasi", command=self.show_notifications).pack(pady=5)
            # Tambahkan tombol/opsi pengguna lainnya

        # --- Tombol Logout ---
        tk.Button(self, text="Logout", command=self.handle_logout, width=20).pack(pady=30)

    def handle_logout(self):
        """Menangani aksi logout."""
        # Reset data pengguna yang login
        self.user_data = None
        messagebox.showinfo("Logout", "Anda telah berhasil logout.")
        # Kembali ke halaman login
        self.main_app.show_login_frame()

    # --- Placeholder methods for navigation ---
    # Metode ini akan dipanggil saat tombol di frame ini diklik
    # MainApp akan mengimplementasikan metode show_..._frame yang sesuai

    def show_manage_items(self):
        """Placeholder untuk navigasi ke halaman kelola barang (Admin)."""
        print("Navigasi ke halaman Kelola Barang (Admin)")
        # self.main_app.show_manage_items_frame() # Panggil metode di MainApp

    def show_verify_claims(self):
        """Placeholder untuk navigasi ke halaman verifikasi klaim (Admin)."""
        print("Navigasi ke halaman Verifikasi Klaim (Admin)")
        # self.main_app.show_verify_claims_frame() # Panggil metode di MainApp

    def show_manage_users(self):
        """Placeholder untuk navigasi ke halaman kelola pengguna (Admin)."""
        print("Navigasi ke halaman Kelola Pengguna (Admin)")
        # self.main_app.show_manage_users_frame() # Panggil metode di MainApp

    def show_view_found_items(self):
        """Placeholder untuk navigasi ke halaman lihat barang ditemukan (Pengguna)."""
        print("Navigasi ke halaman Lihat Barang Ditemukan")
        # self.main_app.show_view_found_items_frame() # Panggil metode di MainApp

    def show_report_item(self):
        """Placeholder untuk navigasi ke halaman laporkan barang (Pengguna)."""
        print("Navigasi ke halaman Laporkan Barang Ditemukan")
        # self.main_app.show_report_item_frame() # Panggil metode di MainApp

    def show_my_claims(self):
        """Placeholder untuk navigasi ke halaman lihat klaim saya (Pengguna)."""
        print("Navigasi ke halaman Lihat Klaim Saya")
        # self.main_app.show_my_claims_frame() # Panggil metode di MainApp

    def show_notifications(self):
        """Placeholder untuk navigasi ke halaman notifikasi (Pengguna)."""
        print("Navigasi ke halaman Notifikasi")
        # self.main_app.show_notifications_frame() # Panggil metode di MainApp


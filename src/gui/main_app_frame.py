# src/gui/main_app_frame.py

import tkinter as tk
from tkinter import ttk # Menggunakan ttk untuk widget seperti Frame atau Button
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil jumlah notifikasi belum dibaca
from src.database.notification_dao import get_unread_notifications_count # Import fungsi baru

class MainAppFrame(BaseFrame):
    """
    Frame untuk halaman utama aplikasi setelah pengguna login.
    Menampilkan informasi pengguna dan opsi navigasi ke fitur lain.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi MainAppFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.user_data = None # Untuk menyimpan data pengguna yang login

        # Frame untuk menampung konten utama
        # Widget ini dibuat di __init__ dan tidak dihancurkan oleh clear_widgets
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(expand=True, fill='both', padx=20, pady=20) # Tambahkan padding

        # Variabel untuk menyimpan jumlah notifikasi belum dibaca
        self.unread_notifications_count = 0
        # Label atau teks tombol notifikasi akan diupdate secara berkala

        # create_widgets TIDAK dipanggil di sini lagi
        # self.create_widgets() # <--- HAPUS BARIS INI

    def create_widgets(self):
        """Membuat widget untuk frame utama aplikasi."""
        # self.clear_widgets() # <--- HAPUS BARIS INI. Widget akan dihapus secara manual jika perlu.

        # Bersihkan widget dari content_frame sebelum membuatnya kembali
        # Ini penting jika create_widgets dipanggil ulang (misal di show())
        for widget in self.content_frame.winfo_children():
            widget.destroy()


        # Label Selamat Datang
        # Teks akan diupdate di set_user_data
        self.label_welcome = tk.Label(self.content_frame, text="Selamat Datang", font=('Arial', 20, 'bold'))
        self.label_welcome.pack(pady=(20, 10))

        # Label Informasi Pengguna (akan diupdate di set_user_data)
        self.label_user_info = tk.Label(self.content_frame, text="", font=('Arial', 12))
        self.label_user_info.pack(pady=(0, 30))

        # Frame untuk menampung tombol-tombol navigasi
        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(pady=10)

        # Tombol Laporkan Barang Ditemukan
        tk.Button(button_frame, text="Laporkan Barang Ditemukan", command=self.main_app.show_report_item_frame, width=30, height=2).grid(row=0, column=0, padx=10, pady=10)

        # Tombol Lihat Barang Ditemukan
        tk.Button(button_frame, text="Lihat Barang Ditemukan", command=self.main_app.show_view_items_frame, width=30, height=2).grid(row=0, column=1, padx=10, pady=10)

        # Tombol Lihat Klaim Saya
        tk.Button(button_frame, text="Lihat Klaim Saya", command=self.main_app.show_my_claims_frame, width=30, height=2).grid(row=1, column=0, padx=10, pady=10)

        # Tombol Notifikasi
        # Teks tombol akan diupdate nanti dengan jumlah notifikasi belum dibaca
        self.button_notifications = tk.Button(button_frame, text="Notifikasi", command=self.main_app.show_notifications_frame, width=30, height=2)
        self.button_notifications.grid(row=1, column=1, padx=10, pady=10)


        # Tombol Panel Admin (Awalnya Dibuat, Visibilitas Diatur di set_user_data)
        # Gunakan grid() untuk menempatkannya, tapi simpan referensi agar bisa diatur visibilitasnya
        self.button_admin_panel = tk.Button(button_frame, text="Panel Admin", command=self.main_app.show_admin_panel_frame, width=30, height=2, bg="lightblue") # Warna berbeda untuk admin
        # Jangan panggil .grid() di sini secara langsung, panggil di set_user_data
        # self.button_admin_panel.grid(row=1, column=1, padx=10, pady=10)


        # TODO: Tambahkan tombol atau link lain di sini
        # Misalnya:
        # - Lihat Barang Hilang (jika ada fitur pelaporan barang hilang)
        # - Pengaturan Akun

        # Tombol Logout
        tk.Button(self.content_frame, text="Logout", command=self.handle_logout, width=20).pack(pady=30)

        # Simpan referensi ke button_frame agar bisa diakses di set_user_data
        self.button_frame = button_frame


    def set_user_data(self, user_data):
        """
        Mengatur data pengguna yang login dan memperbarui tampilan.
        Dipanggil oleh MainApp setelah login berhasil.
        """
        print(f"MainAppFrame: set_user_data called with user_data: {user_data}") # DEBUG PRINT
        self.user_data = user_data
        if self.user_data:
            # TODO: Ambil FullName, RoleName, NIM_NIP dari user_data jika sudah ditambahkan di MainApp
            # Untuk saat ini, gunakan UserID dan status admin
            username = self.user_data.get('Username', 'Pengguna') # Asumsi username ada di user_data
            is_admin = self.user_data.get('IsAdmin', False)
            user_id = self.user_data.get('UserID', 'N/A')

            welcome_text = f"Selamat Datang, {username}!"
            info_text = f"UserID: {user_id} | Status: {'Admin' if is_admin else 'Pengguna Biasa'}"
            # TODO: Jika FullName, RoleName, NIM_NIM tersedia di user_data, gunakan itu
            # info_text = f"Nama: {self.user_data.get('FullName', 'N/A')} | NIM/NIP: {self.user_data.get('NIM_NIP', 'N/A')} | Peran: {self.user_data.get('RoleName', 'N/A')}"


            # Periksa apakah widget sudah dibuat sebelum mencoba mengkonfigurasinya
            if hasattr(self, 'label_welcome'):
                 self.label_welcome.config(text=welcome_text)
            if hasattr(self, 'label_user_info'):
                 self.label_user_info.config(text=info_text)

            # --- Logika untuk menampilkan/menyembunyikan tombol Admin Panel ---
            if hasattr(self, 'button_admin_panel'):
                 if is_admin:
                      # Tampilkan tombol admin panel di grid
                      self.button_admin_panel.grid(row=2, column=0, padx=10, pady=10) # Pindahkan ke row 2, col 0
                 else:
                      # Sembunyikan tombol admin panel
                      self.button_admin_panel.grid_forget()


        else:
            # Jika user_data None (misal setelah logout), reset tampilan
            # Periksa apakah widget sudah dibuat sebelum mencoba mengkonfigurasinya
            if hasattr(self, 'label_welcome'):
                 self.label_welcome.config(text="Selamat Datang")
            if hasattr(self, 'label_user_info'):
                 self.label_user_info.config(text="Silakan Login")
            # Sembunyikan tombol-tombol navigasi jika user tidak login (opsional, tergantung alur)
            # self.content_frame.pack_forget() # Atau sembunyikan frame tombol

            # Pastikan tombol admin juga disembunyikan saat logout
            if hasattr(self, 'button_admin_panel'):
                 self.button_admin_panel.grid_forget()


    def handle_logout(self):
        """
        Menangani aksi saat tombol 'Logout' diklik.
        Mereset data pengguna dan kembali ke halaman login.
        """
        print("User logged out.") # Debugging print
        self.user_data = None # Bersihkan data pengguna yang login
        messagebox.showinfo("Logout Sukses", "Anda telah berhasil logout.")
        self.main_app.show_login_frame() # Kembali ke halaman login

    def update_notification_count(self):
        """
        Mengambil jumlah notifikasi belum dibaca dan memperbarui teks tombol Notifikasi.
        """
        logged_in_user_id = self.user_data.get('UserID') if self.user_data else None

        if logged_in_user_id is not None:
            # Panggil fungsi DAO untuk mendapatkan jumlah notifikasi belum dibaca
            count = get_unread_notifications_count(logged_in_user_id)
            self.unread_notifications_count = count # Simpan jumlahnya

            # Perbarui teks tombol notifikasi
            if count > 0:
                self.button_notifications.config(text=f"Notifikasi ({count})", font=('Arial', 10, 'bold')) # Teks tebal jika ada notifikasi
            else:
                self.button_notifications.config(text="Notifikasi", font=('Arial', 10, 'normal')) # Teks normal jika tidak ada

            print(f"Notification count updated: {count} unread.") # Debugging print

            # Opsional: Jadwalkan pembaruan berikutnya (misal setiap 60 detik)
            # self._after_id = self.after(60000, self.update_notification_count) # Update setiap 60000 ms (60 detik)
            # Simpan ID agar bisa dibatalkan di hide()


        else:
            # Jika user_data tidak ada (seharusnya tidak terjadi di frame ini setelah login)
            self.button_notifications.config(text="Notifikasi", font=('Arial', 10, 'normal'))
            self.unread_notifications_count = 0
            print("User data not available, cannot update notification count.") # Debugging print


    def show(self):
        """Menampilkan frame ini."""
        print("MainAppFrame: show called.") # Debugging print
        super().show() # Panggil metode show dari BaseFrame (pack frame)
        # Panggil create_widgets di sini untuk memastikan UI dibuat/diperbarui saat frame ditampilkan
        self.create_widgets()
        # Panggil set_user_data *setelah* create_widgets selesai
        # self.main_app.user_data sudah diset di show_main_app_frame sebelum show() dipanggil
        self.set_user_data(self.main_app.user_data) # PANGGIL DI SINI
        # Perbarui jumlah notifikasi setiap kali frame ini ditampilkan
        self.update_notification_count()


    def hide(self):
        """Menyembunyikan frame ini."""
        print("MainAppFrame: hide called.") # Debugging print
        super().hide()
        # Batalkan penjadwalan update notifikasi jika ada
        # if hasattr(self, '_after_id') and self._after_id is not None:
        #     self.after_cancel(self._after_id)
        #     self._after_id = None # Reset ID setelah dibatalkan


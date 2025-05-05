# src/gui/my_claims_frame.py

import tkinter as tk
from tkinter import ttk # Menggunakan ttk untuk widget seperti Treeview
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil klaim pengguna
from src.database.claim_dao import get_claims_by_user_id
import datetime # Untuk memformat tanggal

class MyClaimsFrame(BaseFrame):
    """
    Frame untuk menampilkan daftar klaim yang diajukan oleh pengguna yang sedang login.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi MyClaimsFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.user_claims = [] # Untuk menyimpan data klaim pengguna

        # Frame untuk menampung konten (agar bisa discroll jika perlu)
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(expand=True, fill='both')

        # Judul Frame
        tk.Label(self.content_frame, text="Klaim Saya", font=('Arial', 18, 'bold')).pack(pady=(20, 10))

        # Frame untuk menampung daftar klaim (bisa pakai Canvas+Frame atau Treeview)
        # Menggunakan Treeview untuk tampilan tabel yang rapi
        self.claims_tree = ttk.Treeview(self.content_frame, columns=("Item", "Tanggal Klaim", "Status Verifikasi"), show="headings")
        self.claims_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Konfigurasi kolom Treeview
        self.claims_tree.heading("Item", text="Barang yang Diklaim")
        self.claims_tree.heading("Tanggal Klaim", text="Tanggal Klaim")
        self.claims_tree.heading("Status Verifikasi", text="Status Verifikasi")

        # Konfigurasi lebar kolom (opsional)
        self.claims_tree.column("Item", width=200, anchor=tk.W)
        self.claims_tree.column("Tanggal Klaim", width=100, anchor=tk.CENTER)
        self.claims_tree.column("Status Verifikasi", width=150, anchor=tk.CENTER)

        # Tambahkan Scrollbar untuk Treeview
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.claims_tree.yview)
        self.claims_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Link kembali ke halaman utama
        # Menggunakan lambda untuk meneruskan user_data saat tombol diklik
        tk.Button(self.content_frame, text="Kembali ke Halaman Utama", command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data), relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 10))


    def load_claims_data(self):
        """
        Mengambil data klaim dari DAO untuk pengguna yang sedang login.
        """
        logged_in_user_id = self.main_app.user_data.get('UserID') if self.main_app.user_data else None

        if logged_in_user_id is None:
            messagebox.showwarning("Error", "Data pengguna tidak tersedia. Silakan login kembali.")
            self.user_claims = [] # Kosongkan data klaim
            self.main_app.show_login_frame() # Kembali ke login
            return

        print(f"Attempting to load claims for UserID: {logged_in_user_id}") # Debugging print
        self.user_claims = get_claims_by_user_id(logged_in_user_id)
        print(f"Loaded {len(self.user_claims)} claims for UserID: {logged_in_user_id}") # Debugging print


    def display_claims(self):
        """
        Menampilkan data klaim di Treeview.
        """
        # Hapus data lama dari Treeview
        for item in self.claims_tree.get_children():
            self.claims_tree.delete(item)

        if not self.user_claims:
            # Tampilkan pesan jika tidak ada klaim
            # Bisa tambahkan label di bawah Treeview atau di dalam Treeview jika kosong
            # Treeview sudah menampilkan area kosong jika tidak ada data
            print("No claims to display.") # Debugging print
            pass # Tidak perlu menampilkan pesan "Tidak ada klaim" di Treeview itu sendiri

        else:
            # Masukkan data klaim ke Treeview
            for claim in self.user_claims:
                item_name = claim.get('ItemName', 'Nama Barang Tidak Tersedia')
                claim_date = claim.get('ClaimDate')
                # Format tanggal jika itu objek datetime.date atau datetime.datetime
                claim_date_str = claim_date.strftime('%Y-%m-%d') if isinstance(claim_date, (datetime.date, datetime.datetime)) else str(claim_date)
                verification_status = claim.get('VerificationStatus', 'Status Tidak Diketahui')

                self.claims_tree.insert("", tk.END, values=(item_name, claim_date_str, verification_status))
            print("Claims displayed in Treeview.") # Debugging print


    def show(self):
        """
        Menampilkan frame ini dan me-refresh daftar klaim.
        """
        print("MyClaimsFrame: show called.") # Debugging print
        super().show() # Panggil metode show dari BaseFrame (pack frame)
        # Muat data klaim dan tampilkan setiap kali frame ini ditunjukkan
        self.load_claims_data()
        self.display_claims()

    def hide(self):
        """
        Menyembunyikan frame ini.
        """
        print("MyClaimsFrame: hide called.") # Debugging print
        super().hide()
        # Opsional: Bersihkan data klaim saat frame disembunyikan untuk menghemat memori
        self.user_claims = []
        self.display_claims() 

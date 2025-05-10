# src/gui/notifications_frame.py

import tkinter as tk
from tkinter import ttk # Menggunakan ttk untuk widget seperti Treeview
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil notifikasi dan menandainya sebagai sudah dibaca
from src.database.notification_dao import get_notifications_by_user, mark_notification_as_read
import datetime # Untuk memformat tanggal

class NotificationsFrame(BaseFrame):
    """
    Frame untuk menampilkan daftar notifikasi untuk pengguna yang sedang login.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi NotificationsFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.notifications_list = [] # Untuk menyimpan data notifikasi pengguna

        # Frame untuk menampung konten utama
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(expand=True, fill='both')

        # Judul Frame
        tk.Label(self.content_frame, text="Notifikasi Anda", font=('Arial', 18, 'bold')).pack(pady=(20, 10))

        # Frame untuk menampung daftar notifikasi (menggunakan Treeview)
        # Kita akan menampilkan Pesan, Waktu Dikirim, dan Status (Sudah/Belum Dibaca)
        # --- PERBAIKAN: Tambahkan "NotificationID" ke daftar kolom ---
        # Meskipun tidak ditampilkan (karena show="headings"), ini membuat nilai NotificationID
        # tersedia di tuple item_values saat baris dipilih.
        self.notifications_tree = ttk.Treeview(self.content_frame, columns=("Message", "SentAt", "IsRead", "NotificationID"), show="headings")
        self.notifications_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Konfigurasi kolom Treeview
        self.notifications_tree.heading("Message", text="Pesan Notifikasi")
        self.notifications_tree.heading("SentAt", text="Waktu Dikirim")
        self.notifications_tree.heading("IsRead", text="Status") # Status Dibaca/Belum Dibaca
        # --- PERBAIKAN: Konfigurasi kolom NotificationID (sembunyikan) ---
        # Lebar 0 dan stretch=tk.NO akan menyembunyikan kolom ini
        self.notifications_tree.heading("NotificationID", text="ID Notifikasi") # Heading tetap perlu didefinisikan
        self.notifications_tree.column("NotificationID", width=0, stretch=tk.NO)


        # Konfigurasi lebar kolom lain (opsional)
        self.notifications_tree.column("Message", width=400, anchor=tk.W)
        self.notifications_tree.column("SentAt", width=150, anchor=tk.CENTER)
        self.notifications_tree.column("IsRead", width=100, anchor=tk.CENTER)


        # Tambahkan Scrollbar untuk Treeview
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.notifications_tree.yview)
        self.notifications_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Bind event saat baris di Treeview dipilih
        self.notifications_tree.bind("<<TreeviewSelect>>", self.on_notification_select)

        # Link kembali ke halaman utama
        # Menggunakan lambda untuk meneruskan user_data saat tombol diklik
        tk.Button(self.content_frame, text="Kembali ke Halaman Utama", command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data), relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 10))


    def load_notifications_data(self):
        """
        Mengambil data notifikasi dari DAO untuk pengguna yang sedang login.
        """
        logged_in_user_id = self.main_app.user_data.get('UserID') if self.main_app.user_data else None

        if logged_in_user_id is None:
            messagebox.showwarning("Error", "Data pengguna tidak tersedia. Silakan login kembali.")
            self.notifications_list = [] # Kosongkan data notifikasi
            self.main_app.show_login_frame() # Kembali ke login
            return

        print(f"Attempting to load notifications for UserID: {logged_in_user_id}") # Debugging print
        # Ambil semua notifikasi (termasuk yang sudah dibaca)
        self.notifications_list = get_notifications_by_user(logged_in_user_id, include_read=True)
        print(f"Loaded {len(self.notifications_list)} notifications for UserID: {logged_in_user_id}") # Debugging print


    def display_notifications(self):
        """
        Menampilkan data notifikasi di Treeview.
        """
        # Hapus data lama dari Treeview
        for item in self.notifications_tree.get_children():
            self.notifications_tree.delete(item)

        if not self.notifications_list:
            # Tampilkan pesan jika tidak ada notifikasi
            print("No notifications to display.") # Debugging print
            # Anda bisa tambahkan label di bawah Treeview atau di dalam Treeview jika kosong
            # Treeview sudah menampilkan area kosong jika tidak ada data
            pass

        else:
            # Masukkan data notifikasi ke Treeview
            for notification in self.notifications_list:
                # Simpan NotificationID di item Treeview (bisa disembunyikan)
                notification_id = notification.get('NotificationID')
                message = notification.get('Message', 'Pesan Kosong')
                sent_at = notification.get('SentAt')
                # Format tanggal dan waktu
                sent_at_str = sent_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(sent_at, datetime.datetime) else str(sent_at)
                is_read = notification.get('IsRead', False)

                # Tampilkan status 'Sudah Dibaca' atau 'Belum Dibaca'
                status_text = "Sudah Dibaca" if is_read else "Belum Dibaca"

                # Anda bisa menambahkan tag ke item Treeview berdasarkan status read
                # untuk styling visual (misal: teks tebal untuk belum dibaca)
                tags = ('unread',) if not is_read else ('read',)

                # --- PERBAIKAN: Masukkan NotificationID ke dalam tuple values ---
                # Urutan harus sesuai dengan definisi kolom di __init__
                self.notifications_tree.insert("", tk.END, values=(message, sent_at_str, status_text, notification_id), tags=tags)


            # Konfigurasi tag untuk styling (opsional)
            self.notifications_tree.tag_configure('unread', font=('Arial', 10, 'bold')) # Teks tebal untuk belum dibaca
            self.notifications_tree.tag_configure('read', font=('Arial', 10, 'normal')) # Teks normal untuk sudah dibaca

            print("Notifications displayed in Treeview.") # Debugging print


    def on_notification_select(self, event):
        """
        Menangani event saat baris notifikasi di Treeview dipilih.
        Menandai notifikasi yang dipilih sebagai sudah dibaca.
        """
        selected_items = self.notifications_tree.selection() # Ambil item yang dipilih
        if not selected_items:
            return # Tidak ada item yang dipilih

        # Ambil item pertama yang dipilih
        selected_item = selected_items[0]
        # Ambil nilai dari item yang dipilih
        # Nilai di Treeview sekarang adalah (Message, SentAt, IsRead_Text, NotificationID)
        item_values = self.notifications_tree.item(selected_item, 'values')

        # --- PERBAIKAN: Indeks NotificationID sekarang benar di 3 ---
        try:
            # Indeks NotificationID adalah yang terakhir (indeks 3)
            selected_notification_id = item_values[3]
            print(f"Notification selected: ID={selected_notification_id}, Message='{item_values[0][:50]}...'") # Debugging print
        except IndexError:
            # Ini seharusnya tidak terjadi lagi jika kolom NotificationID sudah ditambahkan
            print("Error: Could not get NotificationID from selected Treeview item. Check Treeview columns definition.")
            return # Gagal mendapatkan ID

        # Cek apakah notifikasi ini belum dibaca
        # Kita bisa cek teks status di kolom Treeview, atau cari di self.notifications_list
        # Mencari di self.notifications_list lebih akurat karena menggunakan data asli
        # Menggunakan str() untuk perbandingan karena nilai dari Treeview mungkin string
        notification_data = next((notif for notif in self.notifications_list if str(notif.get('NotificationID')) == str(selected_notification_id)), None)

        if notification_data and not notification_data.get('IsRead'):
            # Jika notifikasi ditemukan di list data asli dan statusnya Belum Dibaca
            print(f"Notification ID {selected_notification_id} is unread. Marking as read...") # Debugging print
            # Panggil fungsi DAO untuk menandai notifikasi sebagai sudah dibaca
            mark_success = mark_notification_as_read(selected_notification_id)

            if mark_success:
                print(f"Notification ID {selected_notification_id} marked as read successfully.") # Debugging print
                # Refresh tampilan notifikasi setelah berhasil menandai dibaca
                self.load_notifications_data()
                self.display_notifications()
                # Opsional: Tampilkan pesan info
                # messagebox.showinfo("Info", "Notifikasi ditandai sebagai sudah dibaca.")
            else:
                print(f"Failed to mark Notification ID {selected_notification_id} as read.") # Debugging print
                # messagebox.showwarning("Gagal", "Gagal menandai notifikasi sebagai sudah dibaca.")
        else:
            print(f"Notification ID {selected_notification_id} is already read or not found in data.") # Debugging print
            # Notifikasi sudah dibaca atau tidak ditemukan di list data, tidak perlu aksi

        # Setelah menangani seleksi, batalkan seleksi di Treeview
        # self.notifications_tree.selection_remove(selected_item) # Opsional: Hapus seleksi setelah diproses


    def show(self):
        """
        Menampilkan frame ini dan me-refresh daftar notifikasi.
        """
        print("NotificationsFrame: show called.") # Debugging print
        super().show() # Panggil metode show dari BaseFrame (pack frame)
        # Muat data notifikasi dan tampilkan setiap kali frame ini ditunjukkan
        self.load_notifications_data()
        self.display_notifications()

    def hide(self):
        """
        Menyembunyikan frame ini.
        """
        print("NotificationsFrame: hide called.") # Debugging print
        super().hide()
        # Opsional: Bersihkan data notifikasi saat frame disembunyikan untuk menghemat memori
        # self.notifications_list = []
        # self.display_notifications() # Bersihkan tampilan Treeview

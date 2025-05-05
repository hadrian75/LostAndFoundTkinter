# src/gui/report_item_frame.py

import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog # Diperlukan untuk memilih file gambar
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk menambahkan item
from src.database.item_dao import add_item
# Mengimpor modul untuk mengunggah gambar dari direktori image_storage
from src.image_storage.imagekit_service import upload_image # Mengimpor fungsi upload_image dari lokasi BARU
import os # Diperlukan untuk mendapatkan nama file dari jalur
import datetime # Diperlukan untuk timestamp jika membuat nama file unik
# Anda mungkin perlu mengimpor modul threading jika unggah gambar memakan waktu lama dan memblokir GUI
# import threading

class ReportItemFrame(BaseFrame):
    """
    Frame untuk form Melaporkan Barang Ditemukan.
    Pengguna mengisi detail barang yang mereka temukan.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi ReportItemFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.image_paths = [] # List untuk menyimpan jalur file gambar yang dipilih
        self.create_widgets() # Panggil metode untuk membuat widget

    def create_widgets(self):
        """Membuat widget untuk form laporan barang."""
        self.clear_widgets() # Bersihkan widget lama jika ada

        tk.Label(self, text="Laporkan Barang Ditemukan", font=('Arial', 18, 'bold')).pack(pady=(20, 10))
        tk.Label(self, text="Mohon isi detail barang yang Anda temukan.", font=('Arial', 12)).pack(pady=(0, 20))

        # Frame untuk input (menggunakan grid untuk layout lebih rapi)
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        # Nama Barang
        tk.Label(input_frame, text="Nama Barang:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_item_name = tk.Entry(input_frame, width=40)
        self.entry_item_name.grid(row=0, column=1, pady=5, padx=5)

        # Deskripsi
        tk.Label(input_frame, text="Deskripsi:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        # Gunakan Text widget untuk deskripsi multi-baris
        self.text_description = tk.Text(input_frame, width=30, height=5, wrap=tk.WORD)
        self.text_description.grid(row=1, column=1, pady=5, padx=5)

        # Lokasi Ditemukan
        tk.Label(input_frame, text="Lokasi Ditemukan:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.entry_location = tk.Entry(input_frame, width=40)
        self.entry_location.grid(row=2, column=1, pady=5, padx=5)

        # Unggah Gambar (Tombol)
        tk.Label(input_frame, text="Gambar:").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        tk.Button(input_frame, text="Pilih Gambar", command=self.select_images).grid(row=3, column=1, sticky='w', pady=5, padx=5)

        # Label untuk menampilkan jumlah gambar yang dipilih
        self.label_image_count = tk.Label(input_frame, text="0 file dipilih")
        self.label_image_count.grid(row=4, column=1, sticky='w', padx=5)


        # Tombol Laporkan
        tk.Button(self, text="Laporkan Barang", command=self.handle_report_item, width=30).pack(pady=10)

        # Link kembali ke halaman utama
        # Menggunakan lambda untuk meneruskan user_data saat tombol diklik
        tk.Button(self, text="Kembali ke Halaman Utama", command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data), relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 0))


    def select_images(self):
        """Membuka dialog file untuk memilih gambar."""
        # Membuka dialog untuk memilih banyak file
        file_paths = filedialog.askopenfilenames(
            title="Pilih Gambar Barang",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
        )
        if file_paths:
            self.image_paths = list(file_paths)
            self.label_image_count.config(text=f"{len(self.image_paths)} file dipilih")
            print(f"Selected image files: {self.image_paths}") # Debugging print

    def handle_report_item(self):
        """Menangani aksi saat tombol Laporkan Barang diklik."""
        item_name = self.entry_item_name.get().strip()
        description = self.text_description.get("1.0", tk.END).strip() # Ambil teks dari Text widget
        location = self.entry_location.get().strip()

        if not all([item_name, description, location]):
            messagebox.showwarning("Input Error", "Nama Barang, Deskripsi, dan Lokasi harus diisi.")
            return

        # --- Implementasi Unggah Gambar ---
        image_urls = []
        upload_errors = False

        if self.image_paths:
             print(f"Attempting to upload {len(self.image_paths)} images...")
             # Anda mungkin perlu menjalankan proses upload di thread terpisah
             # jika unggah memakan waktu lama agar GUI tidak freeze.
             # Untuk saat ini, kita lakukan secara sinkron.

             for i, path in enumerate(self.image_paths):
                 try:
                     # Buat nama file unik di storage, misal: items/username_itemname_timestamp_index.ext
                     # Mengambil username dari data user yang login
                     username = self.main_app.user_data.get('Username', 'unknown_user')
                     file_ext = os.path.splitext(path)[1] # Ambil ekstensi file
                     timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                     # Menggunakan nama file asli + timestamp + index untuk keunikan
                     uploaded_file_name = f"items/{username}_{os.path.basename(path)}_{timestamp}_{i}{file_ext}"

                     # Panggil fungsi upload_image dari imagekit_service
                     print(f"Uploading file {i+1}/{len(self.image_paths)}: {os.path.basename(path)} as '{uploaded_file_name}'...")
                     # Anda bisa menambahkan opsi folder di sini jika perlu, misal options={"folder": "/items/"}
                     upload_response = upload_image(path, uploaded_file_name)

                     if upload_response and hasattr(upload_response, 'url'):
                         image_urls.append(upload_response.url)
                         print(f"Upload successful. URL: {upload_response.url}")
                     else:
                         print(f"Failed to upload image '{os.path.basename(path)}'. Response: {upload_response}")
                         upload_errors = True # Tandai ada error unggah
                         # Lanjutkan ke gambar berikutnya meskipun ada satu yang gagal
                 except Exception as e:
                     print(f"An error occurred during upload of '{os.path.basename(path)}': {e}")
                     upload_errors = True
                     # Lanjutkan ke gambar berikutnya

             if upload_errors:
                 # Beri tahu pengguna jika ada gambar yang gagal diunggah
                 messagebox.showwarning("Unggah Gambar Gagal", "Beberapa gambar gagal diunggah. Barang akan dilaporkan tanpa gambar tersebut.")
        # --- Akhir Implementasi Unggah Gambar ---


        # Pastikan pengguna sedang login untuk mendapatkan UserID penemu
        # UserID disimpan di self.main_app.user_data setelah login berhasil
        found_by_user_id = self.main_app.user_data.get('UserID') if self.main_app.user_data else None

        if found_by_user_id is None:
            messagebox.showerror("Error", "Data pengguna tidak tersedia. Silakan login kembali.")
            self.main_app.show_login_frame() # Kembali ke login
            return

        # Panggil fungsi DAO untuk menambahkan item ke database
        # Teruskan list image_urls yang sudah diisi (mungkin kosong jika tidak ada gambar atau unggah gagal)
        new_item_id = add_item(found_by_user_id, item_name, description, location, image_urls)

        if new_item_id:
            messagebox.showinfo("Sukses", "Barang berhasil dilaporkan!")
            # Bersihkan form setelah sukses
            self.entry_item_name.delete(0, tk.END)
            self.text_description.delete("1.0", tk.END)
            self.entry_location.delete(0, tk.END)
            self.image_paths = [] # Bersihkan list jalur file lokal
            self.label_image_count.config(text="0 file dipilih") # Update label jumlah file
            # Opsional: Kembali ke halaman utama atau halaman daftar item
            self.main_app.show_main_app_frame(self.main_app.user_data) # Kembali ke halaman utama, teruskan data user
        else:
            # add_item sudah menampilkan error database di konsol
            # Tampilkan pesan umum di GUI jika add_item mengembalikan None
            messagebox.showwarning("Gagal", "Gagal melaporkan barang. Mohon coba lagi.")
            # Tetap di halaman laporan agar user bisa coba lagi

    # Metode hide diwarisi dari BaseFrame

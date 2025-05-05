# src/gui/view_items_frame.py

import tkinter as tk
from tkinter import ttk # Menggunakan ttk untuk widget seperti Scrollbar, Frame, Label, Button
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil item yang ditemukan dan gambar item
from src.database.item_dao import get_all_found_items, get_item_images_by_item_id # Impor fungsi baru
# Mengimpor modul untuk menampilkan gambar dari URL
from PIL import ImageTk, Image # Perlu instal Pillow: pip install Pillow
import requests # Perlu instal requests: pip install requests
from io import BytesIO
import threading # Untuk mengunduh gambar di thread terpisah
import datetime # Untuk memformat tanggal

class ViewItemsFrame(BaseFrame):
    """
    Frame untuk menampilkan daftar barang yang ditemukan dalam format postingan.
    Menampilkan detail barang, semua gambar, dan memungkinkan pengguna untuk mengajukan klaim.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi ViewItemsFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.found_items = [] # Untuk menyimpan data item yang ditemukan
        # Dictionary untuk menyimpan referensi gambar item {ItemID: [photo_img1, photo_img2, ...]}
        # Ini penting untuk mencegah gambar dihapus oleh garbage collector
        self.item_image_refs = {}

        # --- Area Konten Utama yang Dapat Di-scroll Vertikal ---
        # Canvas utama untuk membuat area yang bisa di-scroll
        self.main_canvas = tk.Canvas(self, bd=0, highlightthickness=0) # Hapus border default canvas
        self.main_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Scrollbar vertikal untuk main_canvas
        self.main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.main_scrollbar.pack(side="right", fill="y")

        # Konfigurasi canvas agar terhubung dengan scrollbar
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        # Bind event resize untuk update scrollregion
        self.main_canvas.bind('<Configure>', lambda e: self.main_canvas.configure(scrollregion = self.main_canvas.bbox("all")))

        # Frame di dalam canvas untuk menampung semua postingan item
        # Gunakan ttk.Frame untuk tampilan yang lebih modern
        self.scrollable_frame = ttk.Frame(self.main_canvas, padding="10") # Tambahkan padding internal
        # Frame ini akan diperluas oleh canvas
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Judul Frame (di dalam scrollable_frame)
        ttk.Label(self.scrollable_frame, text="Daftar Barang Ditemukan", font=('Arial', 18, 'bold')).pack(pady=(0, 20)) # Kurangi padding atas

        # Link kembali ke halaman utama (di luar area scrollable agar selalu terlihat)
        # Gunakan ttk.Button
        ttk.Button(self, text="Kembali ke Halaman Utama", command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data)).pack(pady=(0, 10))


    def load_items_data(self):
        """
        Mengambil data barang yang ditemukan dari DAO.
        """
        print("ViewItemsFrame: Attempting to load found items.") # Debugging print
        self.found_items = get_all_found_items()
        print(f"ViewItemsFrame: Loaded {len(self.found_items)} found items.") # Debugging print


    def display_items(self):
        """
        Menampilkan data barang yang ditemukan dalam format postingan.
        """
        print("ViewItemsFrame: Displaying items as postings.") # Debugging print
        # Hapus semua widget dari scrollable_frame (semua postingan item sebelumnya)
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Bersihkan referensi gambar lama
        self.item_image_refs = {}

        # Tambahkan kembali judul setelah membersihkan frame
        ttk.Label(self.scrollable_frame, text="Daftar Barang Ditemukan", font=('Arial', 18, 'bold')).pack(pady=(0, 20))


        if not self.found_items:
            print("ViewItemsFrame: No found items to display.") # Debugging print
            ttk.Label(self.scrollable_frame, text="Tidak ada barang ditemukan saat ini.", font=('Arial', 14)).pack(pady=20)
            # Update scrollregion meskipun kosong
            self.scrollable_frame.update_idletasks()
            self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))
            return

        # Masukkan data item sebagai postingan
        for item in self.found_items:
            item_id = item.get('ItemID')
            item_name = item.get('ItemName', 'Nama Barang Tidak Tersedia')
            found_by_username = item.get('FoundByUsername', 'Tidak Diketahui')
            created_at = item.get('CreatedAt')
            # Format tanggal jika itu objek datetime
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if isinstance(created_at, datetime.datetime) else str(created_at) if created_at else '-'
            location = item.get('Location', '-')
            description = item.get('Description', '-')

            # --- Buat Frame untuk Satu Postingan Item ---
            # Gunakan tk.LabelFrame karena ttk.LabelFrame tidak mendukung teks judul dengan mudah
            item_frame = tk.LabelFrame(self.scrollable_frame, text=item_name, padx=15, pady=15, font=('Arial', 14, 'bold')) # Font untuk judul item
            item_frame.pack(fill='x', pady=10, padx=5) # Padding horizontal agar tidak terlalu mepet

            # Detail teks item (menggunakan grid di dalam item_frame untuk layout rapi)
            detail_text_frame = ttk.Frame(item_frame) # Gunakan ttk.Frame
            detail_text_frame.pack(fill='x', pady=(0, 10))

            ttk.Label(detail_text_frame, text=f"Ditemukan Oleh: {found_by_username}", anchor='w').pack(fill='x', pady=2) # Tambahkan padding vertikal kecil
            ttk.Label(detail_text_frame, text=f"Tanggal: {created_at_str}", anchor='w').pack(fill='x', pady=2)
            ttk.Label(detail_text_frame, text=f"Lokasi: {location}", anchor='w').pack(fill='x', pady=2)
            ttk.Label(detail_text_frame, text=f"Deskripsi:", anchor='w').pack(fill='x', pady=(5,0))
            ttk.Label(detail_text_frame, text=description, anchor='w', justify='left', wraplength=500).pack(fill='x') # Wrap text deskripsi

            # --- Area Gambar Item (Dapat Di-scroll Horizontal) ---
            images_outer_frame = ttk.Frame(item_frame) # Frame luar untuk gambar
            images_outer_frame.pack(pady=10, fill='x')
            ttk.Label(images_outer_frame, text="Gambar Barang:", anchor='w').pack(fill='x')

            # Frame menampung Canvas dan Scrollbar horizontal
            images_scroll_container = ttk.Frame(images_outer_frame)
            images_scroll_container.pack(fill='x', expand=True)

            # Canvas untuk menampilkan gambar (jika banyak, bisa discroll horizontal)
            item_images_canvas = tk.Canvas(images_scroll_container, height=150, bd=0, highlightthickness=0) # Hapus border default canvas
            item_images_canvas.pack(side="left", fill="x", expand=True)
            item_images_scrollbar = ttk.Scrollbar(images_scroll_container, orient="horizontal", command=item_images_canvas.xview)
            item_images_canvas.configure(xscrollcommand=item_images_scrollbar.set)
            item_images_scrollbar.pack(side="bottom", fill="x")

            # Frame di dalam canvas untuk menampung gambar-gambar item
            item_images_scrollable_frame = ttk.Frame(item_images_canvas) # Gunakan ttk.Frame
            item_images_canvas.create_window((0, 0), window=item_images_scrollable_frame, anchor="nw")
            # Bind configure event untuk update scrollregion
            item_images_scrollable_frame.bind("<Configure>", lambda e, c=item_images_canvas: c.configure(scrollregion=c.bbox("all")))


            # Muat dan tampilkan semua gambar item
            self.load_and_display_item_images(item_id, item_images_scrollable_frame)


            # --- Tombol Ajukan Klaim untuk Postingan Ini ---
            # Gunakan lambda untuk meneruskan item_id ke handler
            ttk.Button(item_frame, text="Ajukan Klaim untuk Barang Ini", command=lambda item_id=item_id: self.handle_claim_item(item_id)).pack(pady=10)

        # Setelah semua item ditampilkan, update scrollregion untuk main_canvas
        self.scrollable_frame.update_idletasks() # Penting: Update agar bbox() akurat
        self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))
        print("ViewItemsFrame: Finished displaying items.") # Debugging print


    def load_and_display_item_images(self, item_id, images_container_frame):
        """
        Mengambil URL semua gambar untuk item tertentu dari DAO dan menampilkannya.
        Menggunakan threading untuk mengunduh gambar.
        """
        print(f"ViewItemsFrame: Loading all images for ItemID: {item_id}") # Debugging print
        # Panggil fungsi DAO baru untuk mengambil semua URL gambar item
        image_urls = get_item_images_by_item_id(item_id)

        # Inisialisasi list referensi gambar untuk ItemID ini
        self.item_image_refs[item_id] = []

        if not image_urls:
            ttk.Label(images_container_frame, text="[Tidak Ada Gambar]").pack(side="left", padx=5) # Gunakan ttk.Label
            print(f"ViewItemsFrame: No images found for ItemID {item_id}.") # Debugging print
            return

        print(f"ViewItemsFrame: Found {len(image_urls)} images for ItemID {item_id}. Attempting to display...") # Debugging print
        # Gunakan threading untuk mengunduh dan menampilkan gambar
        for url in image_urls:
            # Tampilkan label "Memuat..." sementara
            # Gunakan ttk.Label
            img_label = ttk.Label(images_container_frame, text="Memuat...")
            img_label.pack(side="left", padx=5)
            # Teruskan item_id juga ke fungsi download_and_display_image
            thread = threading.Thread(target=self.download_and_display_image, args=(url, img_label, item_id))
            thread.daemon = True # Set thread as daemon so it exits when the main app exits
            thread.start()


    def download_and_display_image(self, image_url, img_label, item_id):
        """
        Mengunduh gambar dari URL dan menampilkannya di label yang diberikan.
        Dijalankan di thread terpisah.
        """
        try:
            # print(f"ViewItemsFrame: Downloading image from URL: {image_url}") # Debugging print
            response = requests.get(image_url)
            response.raise_for_status() # Cek jika ada error HTTP
            img_data = response.content
            img = Image.open(BytesIO(img_data))

            # Resize gambar agar tidak terlalu besar di GUI
            # Gunakan ukuran yang konsisten, misalnya 120x120
            img.thumbnail((120, 120)) # Ukuran thumbnail untuk gambar item

            photo_img = ImageTk.PhotoImage(img)

            # --- Add check if img_label is still valid ---
            try:
                if img_label.winfo_exists(): # Check if the widget still exists
                    # Update label di thread utama menggunakan after()
                    # Teruskan item_id juga ke update_image_label
                    self.after(0, lambda: self.update_image_label(img_label, photo_img, item_id))
                else:
                    print("ViewItemsFrame: GUI label for image no longer exists, skipping update.")
            except Exception as e:
                 print(f"ViewItemsFrame: Error checking winfo_exists() for image label: {e}")

            # print(f"ViewItemsFrame: Image successfully downloaded from URL: {image_url}") # Debugging print

        except requests.exceptions.RequestException as e:
            print(f"ViewItemsFrame: Failed to download image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                    # Gunakan ttk.Label config
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat (Unduh Error)]", foreground="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"ViewItemsFrame: Error checking winfo_exists() in image error handler: {e_check}")
        except Exception as e:
            print(f"ViewItemsFrame: Failed to display image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                     # Gunakan ttk.Label config
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat]", foreground="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"ViewItemsFrame: Error checking winfo_exists() in image generic error handler: {e_check}")


    def update_image_label(self, img_label, photo_img, item_id):
        """
        Memperbarui widget Label gambar dengan gambar yang dimuat.
        Dijalankan di thread utama menggunakan after().
        """
        # --- Add check if img_label is still valid ---
        try:
            if img_label.winfo_exists(): # Check if the widget still exists
                 # Gunakan ttk.Label config
                img_label.config(image=photo_img, text='') # Hapus teks "Memuat gambar..."
                # Simpan referensi gambar di dictionary self.item_image_refs berdasarkan ItemID
                self.item_image_refs[item_id].append(photo_img)
                # Update scrollregion canvas gambar horizontal setelah gambar ditambahkan
                # Temukan canvas parent dari img_label
                parent_canvas = img_label.winfo_parent() # Ini adalah images_scrollable_frame
                # images_scrollable_frame adalah window di dalam item_images_canvas
                # Kita perlu menemukan item_images_canvas itu sendiri
                # Cara yang lebih andal adalah menyimpan referensi canvas per item, tapi ini lebih sederhana
                # Asumsi struktur widget: Label -> images_scrollable_frame -> item_images_canvas
                # Coba naik 2 level parent
                item_images_canvas = img_label.winfo_parent().winfo_parent()

                # Pastikan item_images_canvas adalah Canvas sebelum mengkonfigurasi
                if isinstance(item_images_canvas, tk.Canvas):
                    item_images_canvas.update_idletasks() # Penting: Update agar bbox() akurat
                    item_images_canvas.config(scrollregion=item_images_canvas.bbox("all"))
                else:
                    print("ViewItemsFrame: Could not find parent Canvas for image label.")


            else:
                print("ViewItemsFrame: GUI label for image no longer exists during update, skipping.")
        except Exception as e:
             print(f"ViewItemsFrame: Error checking winfo_exists() or updating scrollregion in update_image_label: {e}")


    def handle_claim_item(self, item_id):
        """
        Menangani aksi saat tombol 'Ajukan Klaim untuk Barang Ini' diklik.
        Mengarahkan ke frame klaim dengan ItemID yang dipilih.
        """
        print(f"\nViewItemsFrame: handle_claim_item triggered for ItemID: {item_id}.") # DEBUG PRINT
        # Arahkan ke frame Ajukan Klaim, teruskan ItemID yang dipilih
        # MainApp akan memanggil ClaimItemFrame.set_item_id(item_id)
        self.main_app.show_claim_item_frame(item_id)


    def show(self):
        """
        Menampilkan frame ini dan me-refresh daftar barang yang ditemukan.
        """
        print("ViewItemsFrame: show called.") # Debugging print
        # Muat data item dan tampilkan setiap kali frame ini ditunjukkan
        self.load_items_data()
        self.display_items() # Panggil display_items untuk membuat postingan
        super().show() # Panggil metode show dari BaseFrame (pack frame)


    def hide(self):
        """
        Menyembunyikan frame ini.
        """
        print("ViewItemsFrame: hide called.") # Debugging print
        super().hide()
        # Opsional: Bersihkan data item dan tampilan saat frame disembunyikan
        # self.found_items = []
        # self.item_image_refs = {}
        # self.display_items() # Hapus postingan dari tampilan

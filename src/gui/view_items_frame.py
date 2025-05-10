# src/gui/view_items_frame.py

import tkinter as tk
from tkinter import ttk # Menggunakan ttk untuk widget yang lebih modern (misal: Scrollbar)
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil data item
from src.database.item_dao import get_all_found_items, get_item_images_by_item_id
# Mengimpor modul untuk menampilkan gambar dari URL
from PIL import ImageTk, Image # Perlu instal Pillow: pip install Pillow
import requests # Perlu instal requests: pip install requests
from io import BytesIO
import datetime # Untuk memformat tanggal
import threading # Untuk mengunduh gambar di thread terpisah agar GUI tidak freeze

class ViewItemsFrame(BaseFrame):
    """
    Frame untuk menampilkan daftar barang yang ditemukan dalam format postingan.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi ViewItemsFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.items_list = [] # Untuk menyimpan data item yang diambil dari DB
        self.item_images = {} # Dictionary untuk menyimpan referensi gambar agar tidak dihapus garbage collector

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
        # Judul akan dibuat ulang di display_items()

        # Link kembali ke halaman utama (akan dibuat di display_items() sekarang)
        # Gunakan ttk.Button
        # Tombol ini akan dibuat ulang di display_items()


    def _on_mousewheel(self, event):
        """Handler untuk scroll menggunakan mouse wheel."""
        # Sesuaikan kecepatan scroll jika perlu
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_canvas_configure(self, event):
        """Handler untuk event Configure pada Canvas."""
        # Update lebar scrollable_frame agar sesuai dengan lebar canvas
        # Menggunakan itemconfig pada window yang dibuat di create_window
        # find_withtag("all") menemukan semua item di canvas, termasuk window
        # Pastikan hanya mengupdate lebar window jika ada
        for item_id in self.canvas.find_withtag("all"):
             if self.canvas.type(item_id) == 'window':
                  self.canvas.itemconfig(item_id, width=event.width)
                  break # Asumsi hanya ada satu window (scrollable_frame)

        # Pastikan scrollregion diperbarui setelah lebar diubah
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def create_widgets(self):
        """Membuat widget untuk frame tampilan item."""
        # Bersihkan widget lama dari scrollable_frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.item_images = {} # Bersihkan referensi gambar lama

        # Label judul di dalam scrollable_frame
        ttk.Label(self.scrollable_frame, text="Daftar Barang Ditemukan", font=('Arial', 18, 'bold')).pack(pady=(0, 20)) # Kurangi padding atas

        # Ambil data item dari database
        # load_items() dipanggil di show() sebelum create_widgets()

        if not self.items_list:
            ttk.Label(self.scrollable_frame, text="Tidak ada barang ditemukan saat ini.", font=('Arial', 14)).pack(pady=20)
            # Update scrollregion meskipun kosong
            self.scrollable_frame.update_idletasks()
            self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))
        else:
            # Tampilkan setiap item sebagai postingan
            for item in self.items_list:
                self.display_item_post(item)

        # Tambahkan kembali tombol "Kembali ke Halaman Utama" di DALAM scrollable_frame
        ttk.Button(self.scrollable_frame, text="Kembali ke Halaman Utama", command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data)).pack(pady=(20, 10))


        # Setelah semua item dan tombol kembali ditampilkan, update scrollregion untuk main_canvas
        self.scrollable_frame.update_idletasks() # Penting: Update agar bbox() akurat
        self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))
        print("ViewItemsFrame: Finished displaying items.") # Debugging print


    def load_items(self):
        """Mengambil data barang dari DAO."""
        self.items_list = get_all_found_items()
        # print(f"Loaded {len(self.items_list)} items.") # Debugging print


    def display_item_post(self, item):
        """
        Menampilkan satu item sebagai postingan di dalam scrollable_frame.

        Args:
            item (dict): Dictionary yang berisi data satu item.
        """
        # Frame untuk satu postingan item
        # Memberikan border dan padding, serta warna latar belakang
        item_frame = tk.LabelFrame(self.scrollable_frame, text=item.get('ItemName', 'Nama Tidak Tersedia'), padx=15, pady=15, font=('Arial', 14, 'bold')) # Font untuk judul item
        item_frame.pack(fill='x', pady=10, padx=5) # Padding horizontal agar tidak terlalu mepet

        # Detail teks item (menggunakan grid di dalam item_frame untuk layout rapi)
        detail_text_frame = ttk.Frame(item_frame) # Gunakan ttk.Frame
        detail_text_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(detail_text_frame, text=f"Ditemukan Oleh: {item.get('FoundByUsername', 'Tidak Diketahui')}", anchor='w').pack(fill='x', pady=2) # Tambahkan padding vertikal kecil
        created_at = item.get('CreatedAt')
        created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if isinstance(created_at, datetime.datetime) else str(created_at)
        ttk.Label(detail_text_frame, text=f"Tanggal: {created_at_str}", anchor='w').pack(fill='x', pady=2)
        location = item.get('Location', '-')
        ttk.Label(detail_text_frame, text=f"Lokasi: {location}", anchor='w').pack(fill='x', pady=2)
        ttk.Label(detail_text_frame, text=f"Deskripsi:", anchor='w').pack(fill='x', pady=(5,0))
        description = item.get('Description', '-')
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
        # TERUSKAN objek Canvas ke fungsi load_and_display_item_images
        self.load_and_display_item_images(item.get('ItemID'), item_images_scrollable_frame, item_images_canvas) # <-- Teruskan Canvas


        # --- Tombol Ajukan Klaim untuk Postingan Ini ---
        # Gunakan lambda untuk meneruskan item_id ke handler
        # Pastikan user yang login BUKAN admin dan BUKAN penemu barang itu sendiri
        # Cek self.main_app.user_data sebelum mengaksesnya
        is_admin = False # Default jika user_data None
        logged_in_user_id = None # Default jika user_data None
        found_by_user_id = item.get('FoundBy') # Ambil FoundBy dari data item

        if self.main_app.user_data:
             is_admin = self.main_app.user_data.get('IsAdmin', False)
             logged_in_user_id = self.main_app.user_data.get('UserID')

        # Tampilkan tombol klaim hanya jika user_data tersedia, BUKAN admin, dan BUKAN penemu barang
        if self.main_app.user_data and not is_admin and logged_in_user_id != found_by_user_id:
             ttk.Button(item_frame, text="Ajukan Klaim untuk Barang Ini", command=lambda item_id=item.get('ItemID'): self.handle_claim_item(item_id)).pack(pady=10)
        else:
             # Opsional: Tampilkan pesan bahwa barang ditemukan oleh user itu sendiri atau tidak bisa diklaim oleh admin
             # Tampilkan ini hanya jika user_data tersedia
             if self.main_app.user_data: # Hanya tampilkan pesan jika user login
                  if logged_in_user_id == found_by_user_id:
                       ttk.Label(item_frame, text="Ini barang yang Anda temukan.", font=('Arial', 9, 'italic'), foreground="gray").pack(pady=5) # Gunakan foreground
                  # Admin tidak perlu tombol klaim di sini, dan jika user_data None, tidak tampilkan apa-apa


        # Garis pemisah antar postingan (opsional)
        # tk.Frame(self.scrollable_frame, height=1, bg="gray").pack(fill='x', pady=5) # Hapus garis pemisah jika menggunakan border frame


    def load_and_display_item_images(self, item_id, images_container_frame, item_images_canvas):
        """
        Mengambil URL semua gambar untuk item tertentu dari DAO dan menampilkannya.
        Menggunakan threading untuk mengunduh gambar.
        Menerima objek Canvas untuk memperbarui scrollregion.
        """
        print(f"ViewItemsFrame: Loading all images for ItemID: {item_id}") # Debugging print
        # Panggil fungsi DAO baru untuk mengambil semua URL gambar item
        image_urls = get_item_images_by_item_id(item_id)

        # Inisialisasi list referensi gambar untuk ItemID ini
        self.item_images[item_id] = [] # Gunakan self.item_images

        if not image_urls:
            ttk.Label(images_container_frame, text="[Tidak Ada Gambar]").pack(side="left", padx=5) # Gunakan ttk.Label
            print(f"ViewItemsFrame: No images found for ItemID {item_id}.") # Debugging print
            # Perbarui scrollregion meskipun tidak ada gambar agar scrollbar tidak muncul kosong
            item_images_canvas.update_idletasks()
            item_images_canvas.config(scrollregion=item_images_canvas.bbox("all"))
            return

        print(f"ViewItemsFrame: Found {len(image_urls)} images for ItemID {item_id}. Attempting to display...") # Debugging print
        # Gunakan threading untuk mengunduh dan menampilkan gambar
        for url in image_urls:
            # Tampilkan label "Memuat..." sementara
            # Gunakan ttk.Label
            img_label = ttk.Label(images_container_frame, text="Memuat...")
            img_label.pack(side="left", padx=5)
            # Teruskan item_id dan Canvas juga ke fungsi download_and_display_image
            thread = threading.Thread(target=self.download_and_display_image, args=(url, img_label, item_id, item_images_canvas)) # <-- Teruskan Canvas
            thread.daemon = True # Set thread as daemon so it exits when the main app exits
            thread.start()


    def download_and_display_image(self, image_url, img_label, item_id, item_images_canvas):
        """
        Mengunduh gambar dari URL dan menampilkannya di label yang diberikan.
        Dijalankan di thread terpisah.
        Menerima objek Canvas untuk diteruskan ke update_image_label.
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
            # Use try-except around winfo_exists() as well for robustness
            try:
                # Pastikan widget label masih ada sebelum mencoba mengaksesnya
                if img_label.winfo_exists(): # Check if the widget still exists
                    # Update label di thread utama menggunakan after()
                    # Meneruskan item_id dan Canvas juga ke update_image_label
                    self.after(0, lambda: self.update_image_label(img_label, photo_img, item_id, item_images_canvas)) # <-- Teruskan Canvas
                else:
                    print(f"ViewItemsFrame: GUI label for ItemID {item_id} no longer exists, skipping update.") # Debugging print
            except Exception as e:
                 print(f"ViewItemsFrame: Error checking winfo_exists() for ItemID {item_id}: {e}") # Debugging print


            # print(f"ViewItemsFrame: Image successfully downloaded from URL: {image_url}") # Debugging print

        except requests.exceptions.RequestException as e:
            print(f"ViewItemsFrame: Failed to download image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                    # Gunakan ttk.Label config
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat (Unduh Error)]", foreground="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"ViewItemsFrame: Error checking winfo_exists() in image error handler: {e_check}") # Debugging print

        except Exception as e:
            print(f"ViewItemsFrame: Failed to display image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                     # Gunakan ttk.Label config
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat]", foreground="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"ViewItemsFrame: Error checking winfo_exists() in image generic error handler: {e_check}")


    def update_image_label(self, img_label, photo_img, item_id, item_images_canvas):
        """
        Memperbarui widget Label gambar dengan gambar yang dimuat.
        Dijalankan di thread utama menggunakan after().
        Menerima objek Canvas untuk memperbarui scrollregion.
        """
        # --- Add check if img_label is still valid ---
        try:
            if img_label.winfo_exists(): # Check if the widget still exists
                 # Gunakan ttk.Label config
                img_label.config(image=photo_img, text='') # Hapus teks "Memuat gambar..."
                # Simpan referensi gambar di dictionary self.item_images berdasarkan ItemID
                # Pastikan self.item_images[item_id] adalah list
                if item_id not in self.item_images:
                     self.item_images[item_id] = []
                self.item_images[item_id].append(photo_img)

                # Update scrollregion canvas gambar horizontal setelah gambar ditambahkan
                # Gunakan item_images_canvas yang diterima sebagai parameter
                if isinstance(item_images_canvas, tk.Canvas): # Double check type
                    item_images_canvas.update_idletasks() # Penting: Update agar bbox() akurat
                    item_images_canvas.config(scrollregion=item_images_canvas.bbox("all"))
                    # print("ViewItemsFrame: Canvas scrollregion updated.") # Debugging print
                else:
                    print("ViewItemsFrame: Received invalid object instead of Canvas in update_image_label.") # Should not happen if passed correctly

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
        """Menampilkan frame ini dan me-refresh daftar item."""
        print("ViewItemsFrame: show called.") # Debugging print
        super().show() # Panggil metode show dari BaseFrame (pack frame)
        # Muat data item dan tampilkan setiap kali frame ini ditunjukkan
        self.load_items()
        self.create_widgets() # Panggil create_widgets di sini

    def hide(self):
        """Menyembunyikan frame ini."""
        print("ViewItemsFrame: hide called.") # Debugging print
        super().hide()
        # Bersihkan referensi gambar saat frame disembunyikan untuk menghemat memori
        self.item_images = {}
        # Hapus widget dari scrollable_frame saat disembunyikan
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        # Tidak perlu panggil display_items() di hide()


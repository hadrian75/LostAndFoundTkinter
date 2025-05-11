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
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.scrollable_window_id = None # Untuk menyimpan ID window dari scrollable_frame di canvas

        # --- Area Konten Utama yang Dapat Di-scroll Vertikal ---
        # Canvas utama untuk membuat area yang bisa di-scroll
        self.main_canvas = tk.Canvas(self, bd=0, highlightthickness=0) # Hapus border default canvas
        self.main_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Scrollbar vertikal untuk main_canvas
        self.main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.main_scrollbar.pack(side="right", fill="y")

        # Konfigurasi canvas agar terhubung dengan scrollbar
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        
        # Frame di dalam canvas untuk menampung semua postingan item
        self.scrollable_frame = ttk.Frame(self.main_canvas, padding="10")
        # Buat window di canvas untuk scrollable_frame dan simpan ID-nya
        self.scrollable_window_id = self.main_canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw" # Anchor nw, posisi x akan diatur di _on_main_canvas_resize
        )

        # Bind event resize pada main_canvas ke metode _on_main_canvas_resize
        self.main_canvas.bind('<Configure>', self._on_main_canvas_resize)
        # Bind mouse wheel untuk scroll di main_canvas (jika diperlukan dan menargetkan main_canvas)
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel) # Mengikat ke semua widget, atau bind ke self.main_canvas saja

    def _on_main_canvas_resize(self, event=None): # Jadikan event opsional
        """Dipanggil ketika main_canvas diubah ukurannya. Menengahkan scrollable_frame."""
        # Jika event ada dan memiliki atribut width (dari <Configure> asli), gunakan itu.
        # Jika tidak (dipanggil manual), ambil dari winfo_width().
        if event and hasattr(event, 'width'):
            canvas_width = event.width
        else:
            self.main_canvas.update_idletasks() # Pastikan ukuran terbaru
            canvas_width = self.main_canvas.winfo_width()

        # Lanjutkan dengan sisa logika metode...
        self.scrollable_frame.update_idletasks()

        desired_content_width = self.scrollable_frame.winfo_reqwidth()
        max_view_width = 900 
        
        actual_frame_width = desired_content_width
        if desired_content_width > max_view_width:
            actual_frame_width = max_view_width
        if actual_frame_width > canvas_width: 
            actual_frame_width = canvas_width
        
        x_offset = (canvas_width - actual_frame_width) / 2
        if x_offset < 0:
            x_offset = 0

        self.main_canvas.itemconfig(self.scrollable_window_id, width=actual_frame_width)
        self.main_canvas.coords(self.scrollable_window_id, x_offset, 0)
        
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))


    def _on_mousewheel(self, event):
        """Handler untuk scroll menggunakan mouse wheel pada main_canvas."""
        # Pastikan scroll hanya terjadi jika kursor mouse ada di atas main_canvas
        # atau jika main_canvas memiliki fokus. Untuk sederhana, kita asumsikan selalu berlaku.
        # Jika self.main_canvas bukan self.canvas dari kode lama, sesuaikan targetnya.
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Metode _on_canvas_configure yang lama mungkin tidak diperlukan lagi jika _on_main_canvas_resize
    # sudah menangani semua logika resize untuk main_canvas dan scrollable_frame.
    # Jika `self.canvas` di bawah ini adalah `self.main_canvas`, maka ini redundant atau konflik.
    # Saya akan mengomentarinya untuk sementara. Jika ini untuk canvas lain, biarkan.
    # def _on_canvas_configure(self, event):
    #     """Handler untuk event Configure pada Canvas."""
    #     # Update lebar scrollable_frame agar sesuai dengan lebar canvas
    #     # Jika ini adalah self.main_canvas, logika ini akan membuat scrollable_frame
    #     # selalu selebar canvas, yang bertentangan dengan penengahan frame.
    #     # Asumsi self.canvas di sini seharusnya self.main_canvas dan logika ini tidak diinginkan lagi.
    #     # for item_id in self.main_canvas.find_withtag("all"): # Mengganti self.canvas dengan self.main_canvas
    #     #     if self.main_canvas.type(item_id) == 'window' and item_id == self.scrollable_window_id:
    #     #         # Baris ini akan membuat scrollable_frame selebar canvas, hapus jika ingin frame tengah
    #     #         # self.main_canvas.itemconfig(item_id, width=event.width)
    #     #         break 
    #     # self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
    #     pass # Dikosongkan karena _on_main_canvas_resize sudah menghandle


    def create_widgets(self):
        # Clear old widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Add THIS frame to center everything INSIDE scrollable_frame
        # Lebar center_frame akan ditentukan oleh kontennya.
        center_frame = ttk.Frame(self.scrollable_frame) # Tidak perlu border & relief jika scrollable_frame sudah punya padding
        center_frame.pack(expand=False, pady=20, padx=20) # expand=False agar tidak mengisi sisa scrollable_frame, biarkan lebarnya alami
        self.scrollable_frame.update_idletasks()
        if self.main_canvas.winfo_ismapped() and self.main_canvas.winfo_width() > 1:
             self._on_main_canvas_resize() # Panggil tanpa argumen event
        else:
            self.after(50, self._on_main_canvas_resize) 
        ttk.Label(
            center_frame,
            text="Daftar Barang Ditemukan",
            font=('Arial', 18, 'bold')
        ).pack(pady=(0,20))

        if not self.items_list:
            ttk.Label(
                center_frame,
                text="Tidak ada barang ditemukan saat ini.",
                font=('Arial', 14)
            ).pack(pady=10)
        else:
            for item in self.items_list:
                # Item post akan dibuat di dalam scrollable_frame, di bawah center_frame (jika pack digunakan secara berurutan)
                # atau di dalam center_frame jika itu tujuannya.
                # Saat ini, display_item_post menambahkan item_frame ke self.scrollable_frame
                # yang mungkin berarti item akan muncul di bawah center_frame.
                # Jika ingin item juga di dalam center_frame (secara visual), maka display_item_post perlu parent center_frame
                self.display_item_post(self.scrollable_frame, item) # Parent tetap scrollable_frame untuk daftar item

        ttk.Button(
            center_frame, # Tombol kembali tetap di center_frame (judul)
            text="Kembali ke Halaman Utama",
            command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data)
        ).pack(pady=20)

        # Update scroll area setelah semua widget dibuat
        self.scrollable_frame.update_idletasks()
        # Panggil _on_main_canvas_resize secara manual untuk memastikan posisi awal benar
        # Ini penting jika frame ditampilkan tanpa event Configure awal yang signifikan
        if self.main_canvas.winfo_width() > 1 and self.main_canvas.winfo_height() > 1: # Hanya jika canvas sudah punya ukuran
             self._on_main_canvas_resize(tk.Event()) # Kirim event dummy atau buat event dengan width/height
                                                     # Atau lebih baik, panggil dengan parameter eksplisit jika bisa
                                                     # Untuk sekarang, kita andalkan bind <Configure> awal atau saat show.
        # Atau cukup ini, karena <Configure> akan dipanggil saat pack/show
        self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))


    def load_items(self):
        """Mengambil data barang dari DAO."""
        self.items_list = get_all_found_items()
        logging.debug(f"Loaded {len(self.items_list)} items.")
        # logging.debug(self.items_list) # Bisa sangat panjang


    def display_item_post(self, parent_frame, item): # Tambahkan parent_frame
        """
        Menampilkan satu item sebagai postingan di dalam parent_frame.
        Args:
            parent_frame: Frame tempat item post akan dibuat.
            item (dict): Dictionary yang berisi data satu item.
        """
        # Frame tambahan untuk memusatkan item_frame (container_frame sekarang ada di dalam parent_frame)
        # Jika parent_frame adalah scrollable_frame, maka container_frame akan mengisi lebar scrollable_frame
        # yang lebarnya sudah diatur oleh _on_main_canvas_resize
        container_frame = ttk.Frame(parent_frame, borderwidth=1, relief='solid', style='Card.TFrame') # Tambahkan style jika ada
        # container_frame.pack(fill='x', pady=10, padx=10) # padx agar tidak terlalu mepet ke tepi scrollable_frame
        # Untuk memastikan container_frame tidak lebih lebar dari yang diinginkan (misal lebar item_frame)
        # kita pack item_frame dulu baru container_frame membungkusnya, atau atur lebar container_frame.
        # Pendekatan: Buat item_frame dulu, lalu pack container_frame mengelilinginya. Atau lebih sederhana:
        container_frame.pack(pady=10, padx=5, fill='x', expand=False)


        item_frame = tk.LabelFrame(
            container_frame,
            text=item.get('ItemName', 'Nama Tidak Tersedia'),
            padx=15,
            pady=15,
            font=('Arial', 14, 'bold')
        )
        # item_frame di-pack di tengah container_frame jika container_frame lebih lebar.
        # Namun, karena container_frame di-pack fill='x', maka item_frame akan relatif terhadap lebar itu.
        # Jika ingin item_frame sendiri yang menentukan lebar dan berada di tengah scrollable_frame:
        item_frame.pack(anchor='center', fill='none', expand=False, padx=10, pady=5) # expand=False penting

        # ... (sisa kode display_item_post tidak berubah signifikan, pastikan parent widget benar) ...
        detail_text_frame = ttk.Frame(item_frame)
        detail_text_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(detail_text_frame, text=f"Ditemukan Oleh: {item.get('FoundByUsername', 'Tidak Diketahui')}", anchor='w').pack(fill='x', pady=2)
        
        created_at = item.get('CreatedAt')
        created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if isinstance(created_at, datetime.datetime) else str(created_at)
        ttk.Label(detail_text_frame, text=f"Tanggal: {created_at_str}", anchor='w').pack(fill='x', pady=2)
        
        location = item.get('Location', '-')
        ttk.Label(detail_text_frame, text=f"Lokasi: {location}", anchor='w').pack(fill='x', pady=2)
        
        ttk.Label(detail_text_frame, text=f"Deskripsi:", anchor='w').pack(fill='x', pady=(5, 0))
        
        description = item.get('Description', '-')
        # Atur wraplength agar tidak membuat item_frame terlalu lebar jika deskripsi panjang
        # Lebar ini sebaiknya lebih kecil dari max_view_width dikurangi padding
        desc_label = ttk.Label(detail_text_frame, text=description, anchor='w', justify='left', wraplength=650) # Sesuaikan wraplength
        desc_label.pack(fill='x')


        images_outer_frame = ttk.Frame(item_frame)
        images_outer_frame.pack(pady=10, fill='x')
        ttk.Label(images_outer_frame, text="Gambar Barang:", anchor='w').pack(fill='x')

        images_scroll_container = ttk.Frame(images_outer_frame)
        images_scroll_container.pack(fill='x', expand=True)

        item_images_canvas = tk.Canvas(images_scroll_container, height=150, bd=0, highlightthickness=0)
        item_images_canvas.pack(side="left", fill="x", expand=True)
        
        item_images_scrollbar = ttk.Scrollbar(images_scroll_container, orient="horizontal", command=item_images_canvas.xview)
        item_images_canvas.configure(xscrollcommand=item_images_scrollbar.set)
        item_images_scrollbar.pack(side="bottom", fill="x")

        item_images_scrollable_frame = ttk.Frame(item_images_canvas)
        item_images_canvas.create_window((0, 0), window=item_images_scrollable_frame, anchor="nw")
        item_images_scrollable_frame.bind("<Configure>", lambda e, c=item_images_canvas: c.configure(scrollregion=c.bbox("all")))

        self.load_and_display_item_images(item.get('ItemID'), item_images_scrollable_frame, item_images_canvas)

        is_admin = False
        logged_in_user_id = None
        found_by_user_id = int(item.get('FoundBy', -1))

        if self.main_app.user_data:
            is_admin = self.main_app.user_data.get('IsAdmin', False)
            logged_in_user_id = self.main_app.user_data.get('UserID')

        if self.main_app.user_data and not is_admin and logged_in_user_id != found_by_user_id and logged_in_user_id is not None:
            ttk.Button(
                item_frame,
                text="Ajukan Klaim untuk Barang Ini",
                command=lambda item_id=item.get('ItemID'): self.handle_claim_item(item_id)
            ).pack(pady=10, anchor='center')
        elif self.main_app.user_data and logged_in_user_id == found_by_user_id:
            ttk.Label(
                item_frame,
                text="Ini barang yang Anda temukan.",
                font=('Arial', 9, 'italic'),
                foreground="gray"
            ).pack(pady=5, anchor='center')


    def load_and_display_item_images(self, item_id, images_container_frame, item_images_canvas):
        logging.debug(f"ViewItemsFrame: Loading all images for ItemID: {item_id}")
        image_urls = get_item_images_by_item_id(item_id)
        self.item_images[item_id] = []

        if not image_urls:
            ttk.Label(images_container_frame, text="[Tidak Ada Gambar]").pack(side="left", padx=5)
            logging.debug(f"ViewItemsFrame: No images found for ItemID {item_id}.")
            item_images_canvas.update_idletasks()
            item_images_canvas.config(scrollregion=item_images_canvas.bbox("all"))
            return

        logging.debug(f"ViewItemsFrame: Found {len(image_urls)} images for ItemID {item_id}. Attempting to display...")
        for url in image_urls:
            img_label = ttk.Label(images_container_frame, text="Memuat...")
            img_label.pack(side="left", padx=5)
            thread = threading.Thread(target=self.download_and_display_image, args=(url, img_label, item_id, item_images_canvas))
            thread.daemon = True
            thread.start()


    def download_and_display_image(self, image_url, img_label, item_id, item_images_canvas):
        try:
            response = requests.get(image_url, timeout=10) # Tambahkan timeout
            response.raise_for_status()
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img.thumbnail((120, 120))
            photo_img = ImageTk.PhotoImage(img)

            if img_label.winfo_exists():
                self.after(0, lambda: self.update_image_label(img_label, photo_img, item_id, item_images_canvas))
            else:
                logging.warning(f"ViewItemsFrame: GUI label for ItemID {item_id} no longer exists, skipping update.")
        except requests.exceptions.RequestException as e:
            logging.error(f"ViewItemsFrame: Failed to download image from URL {image_url}: {e}")
            if img_label.winfo_exists():
                self.after(0, lambda: img_label.config(text="[Gagal Unduh]", foreground="red", image=''))
        except Exception as e:
            logging.error(f"ViewItemsFrame: Failed to display image from URL {image_url}: {e}")
            if img_label.winfo_exists():
                self.after(0, lambda: img_label.config(text="[Gagal Tampil]", foreground="red", image=''))


    def update_image_label(self, img_label, photo_img, item_id, item_images_canvas):
        try:
            if img_label.winfo_exists():
                img_label.config(image=photo_img, text='')
                if item_id not in self.item_images: # Seharusnya sudah diinisialisasi
                    self.item_images[item_id] = []
                self.item_images[item_id].append(photo_img)

                if isinstance(item_images_canvas, tk.Canvas):
                    item_images_canvas.update_idletasks()
                    item_images_canvas.config(scrollregion=item_images_canvas.bbox("all"))
            else:
                logging.warning("ViewItemsFrame: GUI label for image no longer exists during update, skipping.")
        except Exception as e:
            logging.error(f"ViewItemsFrame: Error updating image label or scrollregion: {e}")


    def handle_claim_item(self, item_id):
        logging.debug(f"\nViewItemsFrame: handle_claim_item triggered for ItemID: {item_id}.")
        self.main_app.show_claim_item_frame(item_id)


    def show(self):
        logging.debug("ViewItemsFrame: show called.")
        super().show()
        self.load_items()
        self.create_widgets()
        # # Memastikan _on_main_canvas_resize dipanggil setelah widget dibuat dan frame ditampilkan
        # # Ini mungkin diperlukan jika <Configure> tidak langsung terpicu dengan benar
        # self.main_canvas.update_idletasks()
        # if self.main_canvas.winfo_width() > 1 : # Pastikan canvas sudah memiliki lebar
        #      # Membuat event object manual untuk Configure
        #     evt = tk.Event()
        #     evt.width = self.main_canvas.winfo_width()
        #     evt.height = self.main_canvas.winfo_height()
        #     self._on_main_canvas_resize(evt)


    def hide(self):
        logging.debug("ViewItemsFrame: hide called.")
        super().hide()
        self.item_images = {}
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
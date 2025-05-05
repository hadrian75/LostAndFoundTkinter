# src/gui/claim_item_frame.py

import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog # Diperlukan untuk memilih file gambar bukti
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil detail item dan menambahkan klaim
from src.database.item_dao import get_item_by_id, get_item_images_by_item_id # Impor fungsi untuk ambil detail dan gambar item
from src.database.claim_dao import add_claim # Impor fungsi untuk menambahkan klaim
# Mengimpor modul untuk mengunggah gambar
from src.image_storage.imagekit_service import upload_image # Mengimpor fungsi upload_image
import os # Diperlukan untuk mendapatkan nama file dari jalur
import datetime # Diperlukan untuk timestamp jika membuat nama file unik
# Mengimpor modul untuk menampilkan gambar dari URL
from PIL import ImageTk, Image # Perlu instal Pillow: pip install Pillow
import requests # Perlu instal requests: pip install requests
from io import BytesIO
import threading # Untuk mengunduh gambar di thread terpisah

class ClaimItemFrame(BaseFrame):
    """
    Frame untuk form Ajukan Klaim Barang.
    Pengguna melihat detail barang yang ditemukan dan mengisi form klaim.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi ClaimItemFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.item_id = None # Untuk menyimpan ItemID barang yang diklaim
        self.item_data = None # Untuk menyimpan detail data item
        self.image_paths = [] # List untuk menyimpan jalur file gambar bukti klaim yang dipilih
        self.item_image_refs = [] # List untuk menyimpan referensi gambar item yang ditampilkan

        # Struktur dasar frame ini akan dibuat di create_widgets()
        # yang dipanggil dari show() setelah item_id diatur.
        # JANGAN panggil create_widgets() di sini!
        # self.create_widgets() # <--- HAPUS BARIS INI

    def set_item_id(self, item_id):
        """
        Mengatur ItemID barang yang akan diklaim di frame ini.
        Dipanggil oleh MainApp sebelum frame ini ditampilkan.
        """
        print(f"ClaimItemFrame: set_item_id called with ItemID: {item_id}") # Debugging print
        self.item_id = item_id
        # Tidak perlu memuat data atau membuat widget di sini.
        # Itu akan dilakukan saat metode show() dipanggil.


    def load_item_data(self):
        """
        Mengambil detail data item dari DAO berdasarkan self.item_id.
        """
        print(f"ClaimItemFrame: load_item_data called for ItemID: {self.item_id}") # Debugging print
        if self.item_id is None:
            print("ClaimItemFrame: ItemID is None in load_item_data, cannot load item data.") # Debugging print
            self.item_data = None
            return

        # Panggil fungsi DAO untuk mengambil detail item
        self.item_data = get_item_by_id(self.item_id)
        print(f"ClaimItemFrame: Item data loaded: {self.item_data is not None}") # Debugging print


    def create_widgets(self):
        """
        Membuat widget (label, entry, tombol) untuk form klaim.
        Widget dibuat berdasarkan self.item_data.
        """
        print(f"ClaimItemFrame: create_widgets called. self.item_id: {self.item_id}, self.item_data is None: {self.item_data is None}") # Debugging print
        self.clear_widgets() # Bersihkan widget lama

        tk.Label(self, text="Ajukan Klaim Barang", font=('Arial', 18, 'bold')).pack(pady=(20, 10))

        # Tampilkan detail barang yang diklaim
        if self.item_data:
            tk.Label(self, text="Detail Barang Diklaim:", font=('Arial', 14, 'underline')).pack(pady=(10, 5))
            # Frame untuk detail item
            item_detail_frame = tk.Frame(self)
            item_detail_frame.pack(pady=5, padx=20, fill='x')

            tk.Label(item_detail_frame, text=f"Nama Barang: {self.item_data.get('ItemName', '-')}", anchor='w').pack(fill='x')
            tk.Label(item_detail_frame, text=f"Deskripsi: {self.item_data.get('Description', '-')}", anchor='w', justify='left', wraplength=600).pack(fill='x')
            tk.Label(item_detail_frame, text=f"Lokasi Ditemukan: {self.item_data.get('Location', '-')}", anchor='w').pack(fill='x')
            tk.Label(item_detail_frame, text=f"Ditemukan Oleh: {self.item_data.get('FoundByUsername', '-')}", anchor='w').pack(fill='x')
            # Format tanggal
            created_at = self.item_data.get('CreatedAt')
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if isinstance(created_at, datetime.datetime) else str(created_at) if created_at else '-'
            tk.Label(item_detail_frame, text=f"Tanggal Ditemukan: {created_at_str}", anchor='w').pack(fill='x')

            # --- Area Gambar Item (Dapat Di-scroll Horizontal) ---
            images_outer_frame = tk.Frame(self) # Frame luar untuk gambar item
            images_outer_frame.pack(pady=10, padx=20, fill='x')
            tk.Label(images_outer_frame, text="Gambar Barang:", anchor='w').pack(fill='x')

            # Frame menampung Canvas dan Scrollbar horizontal
            images_scroll_container = tk.Frame(images_outer_frame)
            images_scroll_container.pack(fill='x', expand=True)

            # Canvas untuk menampilkan gambar item
            item_images_canvas = tk.Canvas(images_scroll_container, height=150, bd=0, highlightthickness=0) # Tinggi tetap untuk gambar
            item_images_canvas.pack(side="left", fill="x", expand=True)
            item_images_scrollbar = tk.Scrollbar(images_scroll_container, orient="horizontal", command=item_images_canvas.xview)
            item_images_canvas.configure(xscrollcommand=item_images_scrollbar.set)
            item_images_scrollbar.pack(side="bottom", fill="x")

            # Frame di dalam canvas untuk menampung gambar-gambar item
            item_images_scrollable_frame = tk.Frame(item_images_canvas)
            item_images_canvas.create_window((0, 0), window=item_images_scrollable_frame, anchor="nw")
            item_images_scrollable_frame.bind("<Configure>", lambda e, c=item_images_canvas: c.configure(scrollregion=c.bbox("all")))

            # Muat dan tampilkan semua gambar item
            self.load_and_display_item_images(self.item_id, item_images_scrollable_frame)


            # --- Form Klaim ---
            tk.Label(self, text="Form Pengajuan Klaim:", font=('Arial', 14, 'underline')).pack(pady=(10, 5))
            claim_form_frame = tk.Frame(self)
            claim_form_frame.pack(pady=5, padx=20, fill='x')

            # Detail Klaim (Textarea)
            tk.Label(claim_form_frame, text="Detail Klaim (Jelaskan mengapa ini milik Anda):", anchor='w').pack(fill='x', pady=5)
            self.text_claim_details = tk.Text(claim_form_frame, width=50, height=5, wrap=tk.WORD)
            self.text_claim_details.pack(fill='x', pady=5)

            # Bukti Gambar Klaim (Tombol Pilih Gambar)
            tk.Label(claim_form_frame, text="Bukti Gambar (Opsional):", anchor='w').pack(fill='x', pady=5)
            tk.Button(claim_form_frame, text="Pilih Bukti Gambar", command=self.select_claim_images).pack(pady=5)
            # Label untuk menampilkan jumlah gambar bukti klaim yang dipilih
            self.label_claim_image_count = tk.Label(claim_form_frame, text="0 file dipilih")
            self.label_claim_image_count.pack(pady=2)


            # Tombol Ajukan Klaim
            tk.Button(self, text="Ajukan Klaim", command=self.handle_submit_claim, width=30).pack(pady=20)

        else:
            # Jika item_data adalah None (item tidak ditemukan atau error)
            tk.Label(self, text="Detail barang tidak tersedia.", font=('Arial', 14), fg='red').pack(pady=20)
            # Tombol Ajukan Klaim tidak perlu ditampilkan jika detail barang tidak tersedia

        # Link kembali ke halaman daftar barang
        # Menggunakan lambda untuk meneruskan user_data saat tombol diklik
        tk.Button(self, text="Kembali ke Daftar Barang", command=self.main_app.show_view_items_frame, relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 0))


    def load_and_display_item_images(self, item_id, images_container_frame):
        """
        Mengambil URL semua gambar untuk item tertentu dari DAO dan menampilkannya.
        Menggunakan threading untuk mengunduh gambar.
        """
        print(f"ClaimItemFrame: Loading all images for ItemID: {item_id}") # Debugging print
        # Panggil fungsi DAO untuk mengambil semua URL gambar item
        image_urls = get_item_images_by_item_id(item_id)

        # Inisialisasi list referensi gambar untuk ItemID ini
        self.item_image_refs = [] # Bersihkan referensi gambar item sebelumnya

        if not image_urls:
            tk.Label(images_container_frame, text="[Tidak Ada Gambar]").pack(side="left", padx=5)
            print(f"ClaimItemFrame: No images found for ItemID {item_id}.") # Debugging print
            return

        print(f"ClaimItemFrame: Found {len(image_urls)} images for ItemID {item_id}. Attempting to display...") # Debugging print
        # Gunakan threading untuk mengunduh dan menampilkan gambar
        for url in image_urls:
            # Tampilkan label "Memuat..." sementara
            img_label = tk.Label(images_container_frame, text="Memuat...")
            img_label.pack(side="left", padx=5)
            # Teruskan item_id juga ke fungsi download_and_display_image
            thread = threading.Thread(target=self.download_and_display_image, args=(url, img_label))
            thread.daemon = True # Set thread as daemon
            thread.start()

    def download_and_display_image(self, image_url, img_label):
        """
        Mengunduh gambar dari URL dan menampilkannya di label yang diberikan.
        Dijalankan di thread terpisah.
        """
        try:
            # print(f"ClaimItemFrame: Downloading image from URL: {image_url}") # Debugging print
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
                    self.after(0, lambda: self.update_image_label(img_label, photo_img))
                else:
                    print("ClaimItemFrame: GUI label for image no longer exists, skipping update.")
            except Exception as e:
                 print(f"ClaimItemFrame: Error checking winfo_exists() for image label: {e}")

            # print(f"ClaimItemFrame: Image successfully downloaded from URL: {image_url}") # Debugging print

        except requests.exceptions.RequestException as e:
            print(f"ClaimItemFrame: Failed to download image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat (Unduh Error)]", fg="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"ClaimItemFrame: Error checking winfo_exists() in image error handler: {e_check}")
        except Exception as e:
            print(f"ClaimItemFrame: Failed to display image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat]", fg="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"ClaimItemFrame: Error checking winfo_exists() in image generic error handler: {e_check}")

    def update_image_label(self, img_label, photo_img):
        """
        Memperbarui widget Label gambar dengan gambar yang dimuat.
        Dijalankan di thread utama menggunakan after().
        """
        # --- Add check if img_label is still valid ---
        try:
            if img_label.winfo_exists(): # Check if the widget still exists
                img_label.config(image=photo_img, text='') # Hapus teks "Memuat gambar..."
                self.item_image_refs.append(photo_img) # Simpan referensi gambar item
                # Update scrollregion canvas gambar horizontal setelah gambar ditambahkan
                # Temukan canvas parent dari img_label
                parent_canvas = img_label.winfo_parent() # Ini adalah images_scrollable_frame
                # images_scrollable_frame adalah window di dalam item_images_canvas
                # Coba naik 2 level parent
                item_images_canvas = img_label.winfo_parent().winfo_parent()

                # Pastikan item_images_canvas adalah Canvas sebelum mengkonfigurasi
                if isinstance(item_images_canvas, tk.Canvas):
                    item_images_canvas.update_idletasks() # Penting: Update agar bbox() akurat
                    item_images_canvas.config(scrollregion=item_images_canvas.bbox("all"))
                else:
                    print("ClaimItemFrame: Could not find parent Canvas for image label.")

            else:
                print("ClaimItemFrame: GUI label for image no longer exists during update, skipping.")
        except Exception as e:
             print(f"ClaimItemFrame: Error checking winfo_exists() or updating scrollregion in update_image_label: {e}")


    def select_claim_images(self):
        """Membuka dialog file untuk memilih gambar bukti klaim."""
        file_paths = filedialog.askopenfilenames(
            title="Pilih Bukti Gambar Klaim",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
        )
        if file_paths:
            self.image_paths = list(file_paths) # Simpan jalur file bukti klaim
            self.label_claim_image_count.config(text=f"{len(self.image_paths)} file dipilih")
            print(f"Selected claim image files: {self.image_paths}") # Debugging print


    def handle_submit_claim(self):
        """Menangani aksi saat tombol Ajukan Klaim diklik."""
        claim_details = self.text_claim_details.get("1.0", tk.END).strip()

        if not claim_details:
            messagebox.showwarning("Input Error", "Detail Klaim harus diisi.")
            return

        if self.item_id is None:
            messagebox.showerror("Error", "Tidak ada barang yang dipilih untuk diklaim.")
            return

        # Pastikan pengguna sedang login untuk mendapatkan UserID pengklaim
        # UserID disimpan di self.main_app.user_data setelah login berhasil
        claimed_by_user_id = self.main_app.user_data.get('UserID') if self.main_app.user_data else None

        if claimed_by_user_id is None:
            messagebox.showerror("Error", "Data pengguna tidak tersedia. Silakan login kembali.")
            self.main_app.show_login_frame() # Kembali ke login
            return

        # --- Implementasi Unggah Gambar Bukti Klaim ---
        claim_image_urls = []
        upload_errors = False

        if self.image_paths:
             print(f"Attempting to upload {len(self.image_paths)} claim images...")
             # Anda mungkin perlu menjalankan proses upload di thread terpisah
             # jika unggah memakan waktu lama agar GUI tidak freeze.
             # Untuk saat ini, kita lakukan secara sinkron.

             for i, path in enumerate(self.image_paths):
                 try:
                     # Buat nama file unik di storage, misal: claims/userid_itemid_timestamp_index.ext
                     username = self.main_app.user_data.get('Username', 'unknown_user')
                     file_ext = os.path.splitext(path)[1] # Ambil ekstensi file
                     timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                     # Menggunakan username + item_id + timestamp + index untuk keunikan
                     uploaded_file_name = f"claims/{username}_{self.item_id}_{timestamp}_{i}{file_ext}"

                     # Panggil fungsi upload_image dari imagekit_service
                     print(f"Uploading claim file {i+1}/{len(self.image_paths)}: {os.path.basename(path)} as '{uploaded_file_name}'...")
                     # Anda bisa menambahkan opsi folder di sini jika perlu, misal options={"folder": "/claims/"}
                     upload_response = upload_image(path, uploaded_file_name)

                     if upload_response and hasattr(upload_response, 'url'):
                         claim_image_urls.append(upload_response.url)
                         print(f"Upload successful. URL: {upload_response.url}")
                     else:
                         print(f"Failed to upload claim image '{os.path.basename(path)}'. Response: {upload_response}")
                         upload_errors = True # Tandai ada error unggah
                         # Lanjutkan ke gambar berikutnya meskipun ada satu yang gagal
                 except Exception as e:
                     print(f"An error occurred during claim image upload of '{os.path.basename(path)}': {e}")
                     upload_errors = True
                     # Lanjutkan ke gambar berikutnya

             if upload_errors:
                 # Beri tahu pengguna jika ada gambar yang gagal diunggah
                 messagebox.showwarning("Unggah Gambar Bukti Gagal", "Beberapa gambar bukti klaim gagal diunggah. Klaim akan diajukan tanpa gambar tersebut.")
        # --- Akhir Implementasi Unggah Gambar Bukti Klaim ---


        # Panggil fungsi DAO untuk menambahkan klaim ke database
        # Teruskan list claim_image_urls yang sudah diisi (mungkin kosong jika tidak ada gambar atau unggah gagal)
        new_claim_id = add_claim(self.item_id, claimed_by_user_id, claim_details, claim_image_urls)

        if new_claim_id:
            messagebox.showinfo("Sukses", "Klaim berhasil diajukan! Mohon tunggu verifikasi oleh admin.")
            # Bersihkan form setelah sukses
            self.text_claim_details.delete("1.0", tk.END)
            self.image_paths = [] # Bersihkan list jalur file lokal bukti klaim
            self.label_claim_image_count.config(text="0 file dipilih") # Update label jumlah file
            self.item_id = None # Reset item_id setelah klaim diajukan
            self.item_data = None # Reset item_data
            # Kembali ke halaman daftar barang
            self.main_app.show_view_items_frame()
        else:
            # add_claim sudah menampilkan error database di konsol
            # Tampilkan pesan umum di GUI jika add_claim mengembalikan None
            messagebox.showwarning("Gagal", "Gagal mengajukan klaim. Mohon coba lagi.")
            # Tetap di halaman klaim agar user bisa coba lagi

    def show(self):
        """
        Menampilkan frame ini, memuat data item, dan membuat widget.
        """
        print("ClaimItemFrame: show called.") # Debugging print
        # Pastikan item_id sudah diatur oleh MainApp sebelum memuat data dan membuat widget
        if self.item_id is not None:
            self.load_item_data() # Muat data item berdasarkan self.item_id
            self.create_widgets() # Buat ulang widget berdasarkan item_data yang dimuat
        else:
            # Jika show dipanggil tanpa item_id diatur (kasus error navigasi)
            print("ClaimItemFrame: show called but self.item_id is None. Displaying error message.") # Debugging print
            self.item_data = None # Pastikan item_data None
            self.create_widgets() # Buat widget (akan menampilkan pesan error)

        super().show() # Panggil metode show dari BaseFrame (pack frame)

    def hide(self):
        """
        Menyembunyikan frame ini.
        """
        print("ClaimItemFrame: hide called.") # Debugging print
        super().hide()
        # Opsional: Bersihkan data dan tampilan saat frame disembunyikan
        # self.item_id = None
        # self.item_data = None
        # self.image_paths = []
        # self.item_image_refs = []
        # self.clear_widgets() # Hapus widget dari tampilan

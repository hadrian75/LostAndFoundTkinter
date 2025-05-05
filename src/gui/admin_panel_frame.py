# src/gui/admin_panel_frame.py

import tkinter as tk
from tkinter import ttk # Menggunakan ttk untuk widget seperti Treeview
from tkinter import messagebox
from .base_frame import BaseFrame # Mengimpor BaseFrame
# Mengimpor fungsi DAO untuk mengambil klaim pending, update status klaim, dan mengambil gambar klaim
from src.database.claim_dao import get_pending_claims, update_claim_status, get_claim_images_by_claim_id # Impor fungsi baru
# Mengimpor fungsi DAO untuk update status item (diperlukan saat klaim disetujui)
from src.database.item_dao import update_item_status # Pastikan fungsi ini ada/akan ada di item_dao.py
import datetime # Untuk memformat tanggal
# Mengimpor modul untuk menampilkan gambar dari URL
from PIL import ImageTk, Image # Perlu instal Pillow: pip install Pillow
import requests # Perlu instal requests: pip install requests
from io import BytesIO
import threading # Untuk mengunduh gambar di thread terpisah

class AdminPanelFrame(BaseFrame):
    """
    Frame untuk Panel Admin.
    Menampilkan klaim yang menunggu verifikasi dan memungkinkan admin untuk menyetujui/menolak.
    Juga menampilkan detail klaim terpilih, termasuk gambar bukti.
    """
    def __init__(self, parent, main_app):
        """
        Inisialisasi AdminPanelFrame.

        Args:
            parent: Widget parent.
            main_app: Referensi ke instance kelas MainApp.
        """
        super().__init__(parent, main_app)
        self.pending_claims = [] # Untuk menyimpan data klaim pending
        self.current_claim_details = None # Untuk menyimpan detail klaim yang sedang ditampilkan
        self.claim_image_refs = [] # List untuk menyimpan referensi gambar klaim yang ditampilkan

        # Frame untuk menampung konten utama
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(expand=True, fill='both')

        # Judul Frame
        tk.Label(self.content_frame, text="Panel Admin: Verifikasi Klaim", font=('Arial', 18, 'bold')).pack(pady=(20, 10))

        # Frame untuk menampung Treeview dan Scrollbar
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Menggunakan Treeview untuk tampilan tabel yang rapi
        self.claims_tree = ttk.Treeview(tree_frame, columns=("ClaimID", "Item", "Pengklaim", "Tanggal Klaim", "Detail Klaim", "ItemID"), show="headings")
        self.claims_tree.pack(side="left", fill="both", expand=True)

        # Konfigurasi kolom Treeview
        # ClaimID dan ItemID disembunyikan ('show="headings"') tapi penting untuk data
        self.claims_tree.heading("ClaimID", text="Claim ID")
        self.claims_tree.heading("Item", text="Barang Diklaim")
        self.claims_tree.heading("Pengklaim", text="Diajukan Oleh")
        self.claims_tree.heading("Tanggal Klaim", text="Tanggal Klaim")
        self.claims_tree.heading("Detail Klaim", text="Detail Klaim")
        self.claims_tree.heading("ItemID", text="Item ID")


        # Konfigurasi lebar kolom (opsional)
        self.claims_tree.column("ClaimID", width=0, stretch=tk.NO) # Sembunyikan kolom ID
        self.claims_tree.column("Item", width=150, anchor=tk.W)
        self.claims_tree.column("Pengklaim", width=150, anchor=tk.W)
        self.claims_tree.column("Tanggal Klaim", width=100, anchor=tk.CENTER)
        self.claims_tree.column("Detail Klaim", width=300, anchor=tk.W)
        self.claims_tree.column("ItemID", width=0, stretch=tk.NO) # Sembunyikan kolom ID


        # Tambahkan Scrollbar untuk Treeview
        self.scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.claims_tree.yview)
        self.claims_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Bind event untuk menampilkan detail klaim saat baris dipilih
        self.claims_tree.bind("<<TreeviewSelect>>", self.on_claim_select)

        # --- Area Detail Klaim Terpilih ---
        self.detail_frame = tk.LabelFrame(self.content_frame, text="Detail Klaim Terpilih", padx=10, pady=10)
        self.detail_frame.pack(pady=10, padx=10, fill='x') # Fill horizontally

        # Label untuk detail teks klaim (akan diupdate saat klaim dipilih)
        self.label_detail_item = tk.Label(self.detail_frame, text="Barang: -", anchor='w', justify='left')
        self.label_detail_item.pack(fill='x', pady=2)
        self.label_detail_claimer = tk.Label(self.detail_frame, text="Pengklaim: -", anchor='w', justify='left')
        self.label_detail_claimer.pack(fill='x', pady=2)
        self.label_detail_date = tk.Label(self.detail_frame, text="Tanggal Klaim: -", anchor='w', justify='left')
        self.label_detail_date.pack(fill='x', pady=2)
        self.label_detail_details = tk.Label(self.detail_frame, text="Detail: -", anchor='w', justify='left', wraplength=600) # Wrap text
        self.label_detail_details.pack(fill='x', pady=2)

        # Frame untuk menampung gambar bukti klaim
        self.images_frame = tk.Frame(self.detail_frame)
        self.images_frame.pack(pady=10, fill='x')
        tk.Label(self.images_frame, text="Bukti Gambar:", anchor='w').pack(fill='x')
        # Canvas untuk menampilkan gambar (jika banyak, bisa discroll)
        # Tinggikan canvas sedikit untuk gambar yang lebih besar
        self.images_canvas = tk.Canvas(self.images_frame, height=180) # Tinggi disesuaikan
        self.images_canvas.pack(side="left", fill="x", expand=True)
        self.images_scrollbar = ttk.Scrollbar(self.images_frame, orient="horizontal", command=self.images_canvas.xview)
        self.images_canvas.configure(xscrollcommand=self.images_scrollbar.set)
        self.images_scrollbar.pack(side="bottom", fill="x")

        # Frame di dalam canvas untuk menampung gambar-gambar
        self.images_scrollable_frame = tk.Frame(self.images_canvas)
        self.images_canvas.create_window((0, 0), window=self.images_scrollable_frame, anchor="nw")
        self.images_scrollable_frame.bind("<Configure>", lambda e: self.images_canvas.configure(scrollregion=self.images_canvas.bbox("all")))


        # Frame untuk tombol aksi admin
        action_frame = tk.Frame(self.content_frame)
        action_frame.pack(pady=10)

        tk.Button(action_frame, text="Setujui Klaim Terpilih", command=self.handle_approve_claim, width=25).grid(row=0, column=0, padx=5)
        tk.Button(action_frame, text="Tolak Klaim Terpilih", command=self.handle_reject_claim, width=25).grid(row=0, column=1, padx=5)

        # Link kembali ke halaman utama admin (atau halaman utama aplikasi)
        tk.Button(self.content_frame, text="Kembali ke Halaman Utama", command=lambda: self.main_app.show_main_app_frame(self.main_app.user_data), relief=tk.FLAT, fg="blue", cursor="hand2").pack(pady=(10, 10))


    def load_pending_claims(self):
        """
        Mengambil data klaim pending dari DAO.
        """
        print("AdminPanelFrame: Attempting to load pending claims.") # Debugging print
        self.pending_claims = get_pending_claims()
        print(f"AdminPanelFrame: Loaded {len(self.pending_claims)} pending claims.") # Debugging print
        # DEBUG: Print loaded claims data
        # print("Loaded claims data structure:")
        # for i, claim in enumerate(self.pending_claims):
        #     print(f"  Claim {i}: {claim}")


    def display_claims(self):
        """
        Menampilkan data klaim pending di Treeview.
        """
        # Hapus data lama dari Treeview
        for item in self.claims_tree.get_children():
            self.claims_tree.delete(item)

        if not self.pending_claims:
            print("AdminPanelFrame: No pending claims to display.") # Debugging print
            # Anda bisa tambahkan label "Tidak ada klaim pending" di sini jika perlu
            pass
        else:
            # Masukkan data klaim ke Treeview
            for claim in self.pending_claims:
                claim_id = claim.get('ClaimID')
                item_id = claim.get('ItemID') # Ambil ItemID
                item_name = claim.get('ItemName', 'Nama Barang Tidak Tersedia')
                claimed_by_name = claim.get('ClaimedByFullName', claim.get('ClaimedByUsername', 'Pengguna Tidak Diketahui')) # Prioritaskan nama lengkap
                claim_date = claim.get('ClaimDate')
                # Format tanggal jika itu objek datetime.date atau datetime.datetime
                claim_date_str = claim_date.strftime('%Y-%m-%d') if isinstance(claim_date, (datetime.date, datetime.datetime)) else str(claim_date)
                claim_details = claim.get('ClaimDetails', 'Tidak ada detail klaim.')
                verification_status = claim.get('VerificationStatus', 'Status Tidak Diketahui') # Seharusnya selalu 'Pending' di sini

                # Masukkan data ke Treeview. Sertakan ClaimID dan ItemID sebagai nilai tersembunyi.
                self.claims_tree.insert("", tk.END, values=(claim_id, item_name, claimed_by_name, claim_date_str, claim_details, item_id))
            print("AdminPanelFrame: Pending claims displayed in Treeview.") # Debugging print


    def on_claim_select(self, event):
        """
        Menangani event saat baris klaim di Treeview dipilih.
        Memuat dan menampilkan detail klaim terpilih, termasuk gambar bukti.
        """
        print("\nAdminPanelFrame: on_claim_select triggered.") # DEBUG PRINT
        selected_item = self.claims_tree.selection() # Ambil item yang dipilih di Treeview
        print(f"AdminPanelFrame: Selected item(s): {selected_item}") # DEBUG PRINT

        # Bersihkan area detail sebelum menampilkan yang baru
        self.clear_detail_area()

        if not selected_item:
            # Tidak ada item yang dipilih atau pilihan dibatalkan
            self.current_claim_details = None
            print("AdminPanelFrame: No claim selected.") # Debugging print
            return

        # Ambil nilai dari item yang dipilih (asumsi hanya satu item dipilih)
        item_values = self.claims_tree.item(selected_item[0], 'values')
        print(f"AdminPanelFrame: Selected item values: {item_values}") # DEBUG PRINT

        # Urutan nilai: (ClaimID, Item, Pengklaim, Tanggal Klaim, Detail Klaim, ItemID)
        # Pastikan indeksnya benar sesuai kolom Treeview
        try:
            selected_claim_id = item_values[0]
            selected_item_id = item_values[5] # ItemID ada di indeks 5
            print(f"AdminPanelFrame: Extracted ClaimID: {selected_claim_id}, ItemID: {selected_item_id}") # DEBUG PRINT
        except IndexError as e:
            print(f"AdminPanelFrame: Error extracting values from selected item: {e}") # DEBUG PRINT
            print("AdminPanelFrame: Check Treeview column definition and item values.")
            return


        # Cari detail klaim lengkap dari self.pending_claims berdasarkan ClaimID
        # self.pending_claims berisi semua detail yang diambil oleh get_pending_claims
        self.current_claim_details = next(
            (claim for claim in self.pending_claims if str(claim.get('ClaimID')) == str(selected_claim_id)), # Bandingkan sebagai string/int jika perlu
            None # Default None jika tidak ditemukan (seharusnya tidak terjadi jika data dari Treeview)
        )

        print(f"AdminPanelFrame: Found claim details: {self.current_claim_details is not None}") # DEBUG PRINT


        if self.current_claim_details:
            print(f"AdminPanelFrame: Displaying details for ClaimID: {selected_claim_id}") # Debugging print
            # Tampilkan detail teks klaim
            self.label_detail_item.config(text=f"Barang: {self.current_claim_details.get('ItemName', '-')}")
            self.label_detail_claimer.config(text=f"Pengklaim: {self.current_claim_details.get('ClaimedByFullName', self.current_claim_details.get('ClaimedByUsername', '-'))}")
            claim_date = self.current_claim_details.get('ClaimDate')
            # Pastikan claim_date bukan None sebelum memformat
            claim_date_str = claim_date.strftime('%Y-%m-%d') if isinstance(claim_date, (datetime.date, datetime.datetime)) else str(claim_date) if claim_date else '-'
            self.label_detail_date.config(text=f"Tanggal Klaim: {claim_date_str}")
            self.label_detail_details.config(text=f"Detail: {self.current_claim_details.get('ClaimDetails', '-')}")

            # Muat dan tampilkan gambar bukti klaim
            self.load_and_display_claim_images(selected_claim_id)

        else:
            # Jika detail klaim tidak ditemukan (kasus error)
            print(f"AdminPanelFrame: Error: Could not find claim details for ClaimID {selected_claim_id} in loaded data.") # Debugging print
            self.label_detail_item.config(text="Barang: Detail tidak tersedia")
            self.label_detail_claimer.config(text="Pengklaim: Detail tidak tersedia")
            self.label_detail_date.config(text="Tanggal Klaim: Detail tidak tersedia")
            self.label_detail_details.config(text="Detail: Detail klaim tidak tersedia.")


    def clear_detail_area(self):
        """
        Membersihkan area detail klaim terpilih dan gambar-gambar bukti.
        """
        print("AdminPanelFrame: Clearing detail area.") # Debugging print
        # Reset label teks detail
        self.label_detail_item.config(text="Barang: -")
        self.label_detail_claimer.config(text="Pengklaim: -")
        self.label_detail_date.config(text="Tanggal Klaim: -")
        self.label_detail_details.config(text="Detail: -")

        # Hapus semua widget gambar dari images_scrollable_frame
        for widget in self.images_scrollable_frame.winfo_children():
            widget.destroy()
        self.claim_image_refs = [] # Bersihkan referensi gambar

        # Reset scrollregion canvas gambar
        self.images_canvas.configure(scrollregion=(0, 0, 0, 0))


    def load_and_display_claim_images(self, claim_id):
        """
        Mengambil URL gambar bukti dari DAO dan menampilkannya.
        Menggunakan threading untuk mengunduh gambar.
        """
        print(f"AdminPanelFrame: Loading images for ClaimID: {claim_id}") # Debugging print
        # Pastikan claim_id adalah integer jika fungsi DAO membutuhkannya
        image_urls = get_claim_images_by_claim_id(int(claim_id)) # Pastikan passing integer

        if not image_urls:
            tk.Label(self.images_scrollable_frame, text="[Tidak Ada Bukti Gambar]").pack(side="left", padx=5)
            print("AdminPanelFrame: No claim images found for this claim.") # Debugging print
            return

        print(f"AdminPanelFrame: Found {len(image_urls)} claim images. Attempting to display...") # Debugging print
        # Gunakan threading untuk mengunduh dan menampilkan gambar
        for url in image_urls:
            # Tampilkan label "Memuat..." sementara
            img_label = tk.Label(self.images_scrollable_frame, text="Memuat gambar...")
            img_label.pack(side="left", padx=5)
            thread = threading.Thread(target=self.download_and_display_image, args=(url, img_label))
            thread.daemon = True # Set thread as daemon so it exits when the main app exits
            thread.start()


    def download_and_display_image(self, image_url, img_label):
        """
        Mengunduh gambar dari URL dan menampilkannya di label yang diberikan.
        Dijalankan di thread terpisah.
        """
        try:
            print(f"AdminPanelFrame: Downloading image from URL: {image_url}") # Debugging print
            response = requests.get(image_url)
            response.raise_for_status() # Cek jika ada error HTTP
            img_data = response.content
            img = Image.open(BytesIO(img_data))

            # Resize gambar agar tidak terlalu besar di GUI
            # Ubah ukuran thumbnail menjadi 150x150
            img.thumbnail((150, 150)) # Ukuran thumbnail yang lebih besar

            photo_img = ImageTk.PhotoImage(img)

            # --- Add check if img_label is still valid ---
            try:
                if img_label.winfo_exists(): # Check if the widget still exists
                    # Update label di thread utama menggunakan after()
                    self.after(0, lambda: self.update_image_label(img_label, photo_img))
                else:
                    print("AdminPanelFrame: GUI label for image no longer exists, skipping update.")
            except Exception as e:
                 print(f"AdminPanelFrame: Error checking winfo_exists() for image label: {e}")

            print(f"AdminPanelFrame: Image successfully downloaded from URL: {image_url}") # Debugging print

        except requests.exceptions.RequestException as e:
            print(f"AdminPanelFrame: Failed to download image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat (Unduh Error)]", fg="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"AdminPanelFrame: Error checking winfo_exists() in image error handler: {e_check}")
        except Exception as e:
            print(f"AdminPanelFrame: Failed to display image from URL {image_url}: {e}")
            try:
                if img_label.winfo_exists():
                    self.after(0, lambda: img_label.config(text="[Gambar Gagal Dimuat]", fg="red", image='')) # Update label di thread utama
            except Exception as e_check:
                 print(f"AdminPanelFrame: Error checking winfo_exists() in image generic error handler: {e_check}")


    def update_image_label(self, img_label, photo_img):
        """
        Memperbarui widget Label gambar dengan gambar yang dimuat.
        Dijalankan di thread utama menggunakan after().
        """
        # --- Add check if img_label is still valid ---
        try:
            if img_label.winfo_exists(): # Check if the widget still exists
                img_label.config(image=photo_img, text='') # Hapus teks "Memuat gambar..."
                self.claim_image_refs.append(photo_img) # Simpan referensi gambar
                # Update scrollregion canvas setelah gambar ditambahkan
                self.images_canvas.update_idletasks() # Penting: Update agar bbox() akurat
                self.images_canvas.config(scrollregion=self.images_canvas.bbox("all"))

            else:
                print("AdminPanelFrame: GUI label for image no longer exists during update, skipping.")
        except Exception as e:
             print(f"AdminPanelFrame: Error checking winfo_exists() in update_image_label: {e}")


    def handle_approve_claim(self):
        """Menangani aksi saat tombol 'Setujui Klaim Terpilih' diklik."""
        selected_item = self.claims_tree.selection() # Ambil item yang dipilih di Treeview

        if not selected_item:
            messagebox.showwarning("Peringatan", "Pilih klaim yang ingin disetujui terlebih dahulu.")
            return

        # Ambil nilai dari item yang dipilih
        item_values = self.claims_tree.item(selected_item[0], 'values')
        # Urutan nilai: (ClaimID, Item, Pengklaim, Tanggal Klaim, Detail Klaim, ItemID)
        selected_claim_id = item_values[0]
        selected_item_id = item_values[5] # ItemID ada di indeks 5
        selected_item_name = item_values[1] # Item Name ada di indeks 1

        print(f"AdminPanelFrame: Attempting to approve ClaimID {selected_claim_id} for ItemID {selected_item_id}.") # Debugging print

        # Konfirmasi admin
        confirm = messagebox.askyesno("Konfirmasi Persetujuan", f"Anda yakin ingin MENYETUJui klaim (ID: {selected_claim_id}) untuk barang '{selected_item_name}'?")
        if not confirm:
            return

        # Panggil fungsi DAO untuk update status klaim menjadi 'Approved'
        claim_update_success = update_claim_status(selected_claim_id, 'Approved')

        if claim_update_success:
            # Jika status klaim berhasil diupdate, update juga status item menjadi 'Claimed'
            item_update_success = update_item_status(selected_item_id, 'Claimed')

            if item_update_success:
                 messagebox.showinfo("Sukses", f"Klaim (ID: {selected_claim_id}) disetujui. Status barang diperbarui menjadi 'Claimed'.")
                 # TODO: Kirim notifikasi ke pengklaim dan penemu
                 # Anda perlu mendapatkan UserID pengklaim (dari self.current_claim_details atau query tambahan)
                 # dan UserID penemu (dari item_dao.get_item_by_id atau JOIN di get_pending_claims)
                 # self.main_app.send_notification(pengklaim_user_id, "Klaim Anda disetujui!")
                 # self.main_app.send_notification(penemu_user_id, f"Barang '{selected_item_name}' yang Anda temukan telah diklaim.")

            else:
                 # Status klaim berhasil diupdate, tapi status item gagal
                 messagebox.showwarning("Peringatan", f"Klaim (ID: {selected_claim_id}) disetujui, tetapi GAGAL memperbarui status barang (ID: {selected_item_id}). Mohon periksa log atau database.")
                 # TODO: Kirim notifikasi ke pengklaim bahwa klaim disetujui, tapi tambahkan catatan tentang masalah item
                 # self.main_app.send_notification(pengklaim_user_id, "Klaim Anda disetujui, tetapi ada masalah dengan status barang.")


            # Refresh daftar klaim pending setelah aksi
            self.load_pending_claims()
            self.display_claims()
            self.clear_detail_area() # Bersihkan detail area setelah klaim diproses

        else:
            # Gagal update status klaim
            messagebox.showwarning("Gagal", f"Gagal menyetujui klaim (ID: {selected_claim_id}). Mohon coba lagi atau periksa log database.")


    def handle_reject_claim(self):
        """Menangani aksi saat tombol 'Tolak Klaim Terpilih' diklik."""
        selected_item = self.claims_tree.selection() # Ambil item yang dipilih di Treeview

        if not selected_item:
            messagebox.showwarning("Peringatan", "Pilih klaim yang ingin ditolak terlebih dahulu.")
            return

        # Ambil nilai dari item yang dipilih
        item_values = self.claims_tree.item(selected_item[0], 'values')
        # Urutan nilai: (ClaimID, Item, Pengklaim, Tanggal Klaim, Detail Klaim, ItemID)
        selected_claim_id = item_values[0]
        selected_item_name = item_values[1] # Ambil nama item untuk pesan konfirmasi

        print(f"AdminPanelFrame: Attempting to reject ClaimID {selected_claim_id} for item '{selected_item_name}'.") # Debugging print


        # Konfirmasi admin
        confirm = messagebox.askyesno("Konfirmasi Penolakan", f"Anda yakin ingin MENOLAK klaim (ID: {selected_claim_id}) untuk barang '{selected_item_name}'?")
        if not confirm:
            return

        # Panggil fungsi DAO untuk update status klaim menjadi 'Rejected'
        claim_update_success = update_claim_status(selected_claim_id, 'Rejected')

        if claim_update_success:
            messagebox.showinfo("Sukses", f"Klaim (ID: {selected_claim_id}) berhasil ditolak.")
            # TODO: Kirim notifikasi ke pengklaim bahwa klaim ditolak
            # Anda perlu mendapatkan UserID pengklaim (dari self.current_claim_details atau query tambahan)
            # self.main_app.send_notification(pengklaim_user_id, "Klaim Anda ditolak.")

            # Refresh daftar klaim pending setelah aksi
            self.load_pending_claims()
            self.display_claims()
            self.clear_detail_area() # Bersihkan detail area setelah klaim diproses

        else:
            # Gagal update status klaim
            messagebox.showwarning("Gagal", f"Gagal menolak klaim (ID: {selected_claim_id}). Mohon coba lagi atau periksa log database.")


    def show(self):
        """
        Menampilkan frame ini dan me-refresh daftar klaim pending.
        """
        print("AdminPanelFrame: show called.") # Debugging print
        # Muat data klaim pending dan tampilkan setiap kali frame ini ditunjukkan
        self.load_pending_claims()
        self.display_claims()
        self.clear_detail_area() # Bersihkan detail area saat frame ditampilkan
        super().show() # Panggil metode show dari BaseFrame (pack frame)


    def hide(self):
        """
        Menyembunyikan frame ini.
        """
        print("AdminPanelFrame: hide called.") # Debugging print
        super().hide()
        # Opsional: Bersihkan data klaim pending saat frame disembunyikan
        self.pending_claims = []
        self.display_claims() 
        self.clear_detail_area() 

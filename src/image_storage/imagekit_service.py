# src/image_storage/imagekit_service.py

from imagekitio import ImageKit
# Mengimpor konfigurasi ImageKit.io dari src.config
from src.config import IMAGEKIT_CONFIG
import os # Diperlukan untuk mengecek keberadaan file

# --- Inisialisasi Klien ImageKit.io ---
# Klien ImageKit.io diinisialisasi menggunakan konfigurasi dari config.py
try:
    # Pastikan IMAGEKIT_CONFIG memiliki kunci 'private_key', 'public_key', dan 'url_endpoint'
    # dan nilai-nilainya tidak None (sudah dimuat dari .env)
    if not all([IMAGEKIT_CONFIG.get('private_key'), IMAGEKIT_CONFIG.get('public_key'), IMAGEKIT_CONFIG.get('url_endpoint')]):
         print("Kesalahan konfigurasi ImageKit.io: Kunci atau URL endpoint tidak lengkap di config.py atau .env.")
         imagekit = None # Set None jika konfigurasi tidak lengkap
    else:
        imagekit = ImageKit(
            private_key=IMAGEKIT_CONFIG['private_key'],
            public_key=IMAGEKIT_CONFIG['public_key'],
            url_endpoint=IMAGEKIT_CONFIG['url_endpoint']
        )
        print("Klien ImageKit.io berhasil diinisialisasi.") # Opsional: untuk debugging
except Exception as e:
    # Menampilkan error jika inisialisasi gagal (misal: kunci salah, format salah)
    print(f"Error inisialisasi ImageKit.io: {e}")
    imagekit = None # Set None jika gagal agar tidak crash saat digunakan

# --- Fungsi untuk Interaksi ImageKit.io ---

def upload_image(file_path, file_name, options=None):
    """
    Mengunggah file gambar ke ImageKit.io.

    Args:
        file_path (str): Jalur lengkap ke file gambar lokal.
        file_name (str): Nama yang diinginkan untuk file di ImageKit.io.
        options (dict, optional): Opsi tambahan untuk unggahan (lihat dokumentasi ImageKit.io).

    Returns:
        object: Objek response dari ImageKit.io (memiliki atribut seperti url, fileId, dll.), atau None jika gagal.
                Kembalikan objek response agar GUI bisa mengakses response.url.
    """
    if imagekit is None:
        print("ImageKit.io client tidak terinisialisasi. Unggah dibatalkan.")
        return None

    # Periksa apakah file_path valid dan file ada
    if not os.path.exists(file_path):
        print(f"Gagal mengunggah: File tidak ditemukan di jalur '{file_path}'.")
        return None

    try:
        # Membaca file dalam mode binary
        with open(file_path, "rb") as file:
            upload_response = imagekit.upload_file(
                file=file, # File object atau bytes
                file_name=file_name, # Nama file di ImageKit.io
                options=options or {} # Gunakan opsi yang diberikan atau dictionary kosong
            )
        # print(f"Unggah berhasil: {upload_response.url}") # Opsional: untuk debugging
        # Objek upload_response memiliki atribut seperti file_id, name, url, thumbnail_url, height, width, dll.
        return upload_response

    except Exception as e:
        print(f"Gagal mengunggah gambar ke ImageKit.io: {e}")
        return None

# --- Test Block ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan imagekit_service.py langsung
    print("Testing ImageKit.io upload...")

    # Pastikan Anda memiliki file dummy atau file gambar asli untuk diunggah
    # Ganti dengan jalur file yang valid di komputer Anda
    test_file_path = "src\image_storage\dummy\dum.png" # <--- GANTI DENGAN JALUR FILE ASLI
    test_file_name = "test_upload/my_test_image.png" # Nama file di ImageKit.io, bisa pakai folder

    # Cek apakah file ada sebelum mencoba mengunggah
    if os.path.exists(test_file_path):
        print(f"Attempting to upload '{test_file_path}' to ImageKit.io as '{test_file_name}'...")
        # Anda bisa menambahkan opsi folder di sini jika perlu, misal options={"folder": "/test_uploads/"}
        # options = {"folder": "/items_test/"} # Contoh opsi folder
        options = {} # Tanpa opsi tambahan

        response = upload_image(test_file_path, test_file_name, options=options)

        if response:
            print("\nImageKit.io upload successful!")
            print(f"  File ID: {response.file_id}")
            print(f"  Name: {response.name}")
            print(f"  URL: {response.url}")
            # Anda bisa tambahkan langkah untuk menghapus file di ImageKit.io setelah test jika diinginkan
            # try:
            #     delete_response = imagekit.delete_file(file_id=response.file_id)
            #     print(f"  Deleted file with ID: {response.file_id}")
            # except Exception as e:
            #     print(f"  Failed to delete file with ID {response.file_id}: {e}")

        else:
            print("\nImageKit.io upload failed.")
            print("Periksa konfigurasi ImageKit.io di .env dan config.py, serta koneksi internet Anda.")

    else:
        print(f"\nFile uji tidak ditemukan: {test_file_path}")
        print("Mohon ganti 'test_file_path' dengan jalur file gambar yang valid di komputer Anda.")



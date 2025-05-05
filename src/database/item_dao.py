# src/database/item_dao.py

import mysql.connector
import datetime
# Mengimpor fungsi koneksi database dari db_connector
from src.database.db_connector import create_db_connection, close_db_connection
# Anda mungkin perlu mengimpor modul untuk mengunggah gambar (misal: ImageKit.io service)
# from src.firebase.imagekit_service import upload_image # Asumsi menggunakan ImageKit.io

def get_all_found_items():
    """
    Mengambil daftar semua barang yang statusnya 'Found' dan aktif dari database.
    Mengembalikan list of dictionaries, di mana setiap dictionary merepresentasikan satu item.
    Mengembalikan list kosong jika tidak ada item ditemukan atau jika terjadi error.
    """
    print("Attempting to fetch all 'Found' items from DB...") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi, kembalikan list kosong

    # Menggunakan dictionary=True agar hasil query mudah diakses dengan nama kolom
    cursor = conn.cursor(dictionary=True)
    items_list = []

    try:
        # Query untuk mengambil item dengan status 'Found' dan IsActive=TRUE
        # Join dengan Users untuk mendapatkan username penemu
        # Tidak perlu join ke ItemImages di sini, kita akan ambil gambar secara terpisah per item
        sql = """
            SELECT
                I.ItemID,
                I.ItemName,
                I.Description,
                I.Location, -- Ambil kolom Location (pastikan sudah ada di skema)
                I.CreatedAt,
                U.Username AS FoundByUsername -- Ambil username penemu jika ada
            FROM
                Items I
            LEFT JOIN -- Gunakan LEFT JOIN karena FoundBy bisa NULL
                Users U ON I.FoundBy = U.UserID
            WHERE
                I.Status = 'Found' AND I.IsActive = TRUE
            ORDER BY
                I.CreatedAt DESC -- Urutkan berdasarkan waktu penemuan terbaru
        """
        cursor.execute(sql)
        items_list = cursor.fetchall() # Ambil semua baris hasil

        print(f"Found {len(items_list)} 'Found' items.") # Debugging print
        return items_list

    except mysql.connector.Error as err:
        print(f"Database Error in get_all_found_items: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)

def get_item_by_id(item_id):
    """
    Mengambil detail satu item berdasarkan ItemID.
    Mengembalikan dictionary data item jika ditemukan, None jika tidak.
    """
    print(f"Attempting to fetch item with ItemID: {item_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    item_data = None

    try:
        # Query untuk mengambil detail item
        # Tidak perlu join ke ItemImages di sini, kita akan ambil gambar secara terpisah
        sql = """
            SELECT
                I.ItemID,
                I.ItemName,
                I.Description,
                I.Location,
                I.CreatedAt,
                U.Username AS FoundByUsername,
                I.Status, -- Ambil juga status item
                I.IsActive -- Ambil juga status aktif item
            FROM
                Items I
            LEFT JOIN
                Users U ON I.FoundBy = U.UserID
            WHERE
                I.ItemID = %s -- Tidak perlu cek IsActive di sini jika ingin melihat detail item yang tidak aktif
        """
        cursor.execute(sql, (item_id,))
        item_data = cursor.fetchone() # Ambil satu baris hasil

        if item_data:
            print(f"Item found: {item_data.get('ItemName')}") # Debugging print
        else:
            print(f"Item with ItemID {item_id} not found.") # Debugging print

        return item_data

    except mysql.connector.Error as err:
        print(f"Database Error in get_item_by_id: {err}") # Log error
        return None
    finally:
        cursor.close()
        close_db_connection(conn)

def get_item_images_by_item_id(item_id):
    """
    Mengambil daftar URL gambar untuk item tertentu.
    Mengembalikan list of strings (URL gambar) jika ditemukan, list kosong jika tidak atau error.
    """
    print(f"Attempting to fetch item images for ItemID: {item_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi

    cursor = conn.cursor() # Tidak perlu dictionary=True jika hanya mengambil satu kolom
    image_urls = []

    try:
        # Query untuk mengambil semua ImageURL dari tabel ItemImages untuk ItemID tertentu
        sql = "SELECT ImageURL FROM ItemImages WHERE ItemID = %s"
        cursor.execute(sql, (item_id,))
        results = cursor.fetchall() # Ambil semua baris hasil

        # Ekstrak URL dari hasil query (hasilnya adalah list of tuples, misal: [('url1',), ('url2',)])
        image_urls = [row[0] for row in results]

        print(f"Found {len(image_urls)} images for ItemID {item_id}.") # Debugging print
        return image_urls

    except mysql.connector.Error as err:
        print(f"Database Error in get_item_images_by_item_id: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)


def add_item(found_by_user_id, item_name, description, location, image_urls):
    """
    Menyimpan data barang yang ditemukan ke tabel Items dan ItemImages.

    Args:
        found_by_user_id (int): UserID dari pengguna yang menemukan barang.
        item_name (str): Nama barang.
        description (str): Deskripsi barang.
        location (str): Lokasi spesifik barang ditemukan.
        image_urls (list): List URL gambar barang.

    Returns:
        int: ItemID dari barang yang baru ditambahkan jika berhasil, None jika gagal.
    """
    print(f"Attempting to add new item: {item_name} found by UserID {found_by_user_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return None # Gagal koneksi

    cursor = conn.cursor()
    item_id = None

    try:
        conn.start_transaction()

        # 1. Masukkan data ke tabel Items
        # Status default adalah 'Found', IsActive default TRUE
        sql_item = "INSERT INTO Items (FoundBy, ItemName, Description, Location) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_item, (found_by_user_id, item_name, description, location))
        item_id = cursor.lastrowid # Ambil ItemID yang baru dibuat
        print(f"Item inserted with ItemID: {item_id}") # Debugging print


        # 2. Masukkan URL gambar ke tabel ItemImages
        if item_id and image_urls:
            sql_image = "INSERT INTO ItemImages (ItemID, ImageURL) VALUES (%s, %s)"
            image_values = [(item_id, url) for url in image_urls]
            cursor.executemany(sql_image, image_values)
            print(f"Inserted {len(image_urls)} image URLs for ItemID {item_id}.") # Debugging print


        conn.commit()
        print(f"New item (ItemID: {item_id}) and images added successfully.") # Debugging print
        return item_id # Kembalikan ItemID yang baru dibuat

    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error
        print(f"Database Error in add_item: {err}") # Log error
        return None
    except Exception as e:
        conn.rollback()
        print(f"An unexpected error occurred in add_item: {e}") # Log error tak terduga
        return None
    finally:
        cursor.close()
        close_db_connection(conn)

def update_item_status(item_id, new_status):
    """
    Memperbarui status item di tabel Items.
    Juga set IsActive = FALSE jika status diubah menjadi 'Claimed' atau 'Lost'.
    Set IsActive = TRUE jika status diubah menjadi 'Found'.

    Args:
        item_id (int): ItemID dari item yang akan diperbarui.
        new_status (str): Status baru ('Found', 'Claimed', atau 'Lost').

    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    print(f"Attempting to update status for ItemID {item_id} to '{new_status}'") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        # Pastikan new_status adalah nilai yang valid untuk ENUM
        valid_statuses = ['Found', 'Claimed', 'Lost']
        if new_status not in valid_statuses:
            print(f"Invalid status '{new_status}' for item update.")
            return False

        # Jika status diubah menjadi 'Claimed' atau 'Lost', set IsActive menjadi FALSE
        # Jika diubah menjadi 'Found', set IsActive menjadi TRUE
        new_is_active_status = True if new_status == 'Found' else False

        sql = "UPDATE Items SET Status = %s, IsActive = %s WHERE ItemID = %s"
        cursor.execute(sql, (new_status, new_is_active_status, item_id))
        conn.commit() # Commit perubahan

        # Periksa apakah ada baris yang terpengaruh (opsional tapi bagus)
        if cursor.rowcount > 0:
            success = True
            print(f"ItemID {item_id} status updated to '{new_status}' and IsActive set to {new_is_active_status}.")
        else:
            # ItemID tidak ditemukan
            print(f"ItemID {item_id} not found for status update.")
            success = False # Gagal karena item tidak ada

    except mysql.connector.Error as err:
        # conn.rollback() # Rollback jika pakai transaksi
        print(f"Database Error in update_item_status: {err}") # Log error
        success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return success


# TODO: Tambahkan fungsi DAO lain untuk Items (misal: delete_item)
# def delete_item(item_id):
#    ... logika DELETE item berdasarkan ID ...
#    pass


# --- Test Block (Opsional) ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan item_dao.py langsung
    print("Testing item_dao functions...")

    # Pastikan Anda memiliki koneksi database yang berfungsi dan tabel Items/ItemImages
    # serta beberapa data dummy dengan Status='Found' dan IsActive=TRUE
    # Pastikan ada user dengan UserID 1 di tabel Users untuk FoundBy
    # Pastikan ada item dengan ItemID yang memiliki beberapa gambar di tabel ItemImages

    # --- Test get_all_found_items ---
    print("\n--- Testing get_all_found_items ---")
    found_items = get_all_found_items()

    if found_items:
        print("Successfully fetched found items:")
        for item in found_items:
            # Perhatikan, get_all_found_items TIDAK lagi mengembalikan PrimaryImageURL
            print(f"  ItemID: {item.get('ItemID')}, Name: {item.get('ItemName')}, Location: {item.get('Location', 'N/A')}, FoundBy: {item.get('FoundByUsername', 'Unknown')}")
    else:
        print("No 'Found' items found or failed to fetch.")

    # --- Test add_item ---
    # print("\n--- Testing add_item ---")
    # # Pastikan UserID 1 ada di tabel Users
    # test_found_by_user_id = 1
    # test_item_name = "Dompet Kulit Hitam"
    # test_description = "Dompet pria, ada kartu mahasiswa di dalamnya."
    # test_location = "Dekat Perpustakaan, lantai 2" # Lokasi
    # # URL gambar dummy (ganti dengan URL asli jika Anda mengunggah gambar)
    # test_image_urls = [
    #     "https://ik.imagekit.io/ilsoqlnic/dummy_wallet_1.jpg",
    #     "https://ik.imagekit.io/ilsoqlnic/dummy_wallet_2.jpg"
    #     ] # Ganti dengan URL gambar asli jika ada

    # print(f"Attempting to add item: '{test_item_name}'...")
    # new_item_id = add_item(test_found_by_user_id, test_item_name, test_description, test_location, test_image_urls)

    # if new_item_id:
    #     print(f"Item added successfully with ItemID: {new_item_id}")
    #     # Anda bisa cek database secara manual untuk memverifikasi data
    # else:
    #     print("Failed to add item.")

    # --- Test get_item_by_id ---
    # Asumsi ada item dengan ItemID 1 di database Anda
    # test_item_id = 1 # Ganti dengan ItemID yang ada di DB
    # print(f"\n--- Testing get_item_by_id for ItemID {test_item_id} ---")
    # item_data = get_item_by_id(test_item_id)

    # if item_data:
    #     print(f"Successfully fetched item data: {item_data}")
    # else:
    #     print(f"Failed to fetch item with ItemID {test_item_id}.")


    # --- Test get_item_images_by_item_id ---
    # Ganti dengan ItemID yang ada di database Anda dan memiliki gambar di ItemImages
    test_item_id_with_images = 1 # Ganti dengan ItemID yang valid
    print(f"\n--- Testing get_item_images_by_item_id for ItemID {test_item_id_with_images} ---")
    item_images = get_item_images_by_item_id(test_item_id_with_images)

    if item_images:
        print(f"Successfully fetched {len(item_images)} images for ItemID {test_item_id_with_images}:")
        for url in item_images:
            print(f"  Image URL: {url}")
    else:
        print(f"No images found for ItemID {test_item_id_with_images} or failed to fetch.")

  
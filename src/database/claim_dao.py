# src/database/claim_dao.py

import mysql.connector
import datetime
# Mengimpor fungsi koneksi database dari db_connector
from src.database.db_connector import create_db_connection, close_db_connection
# Mengimpor fungsi untuk update item status dari item_dao
from src.database.item_dao import update_item_status # Asumsi fungsi ini ada/akan ada

def add_claim(item_id, claimed_by_user_id, claim_details, proof_image_urls):
    """
    Menyimpan data klaim barang ke tabel Claims dan ClaimImages.

    Args:
        item_id (int): ItemID dari barang yang diklaim.
        claimed_by_user_id (int): UserID dari pengguna yang mengajukan klaim.
        claim_details (str): Detail atau alasan klaim.
        proof_image_urls (list): List URL gambar bukti klaim.

    Returns:
        int: ClaimID dari klaim yang baru ditambahkan jika berhasil, None jika gagal.
    """
    print(f"Attempting to add new claim for ItemID {item_id} by UserID {claimed_by_user_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return None # Gagal koneksi

    cursor = conn.cursor()
    claim_id = None

    try:
        conn.start_transaction()

        # 1. Masukkan data ke tabel Claims
        # ClaimDate otomatis diisi oleh database (CURDATE())
        # VerificationStatus default adalah 'Pending'
        sql_claim = "INSERT INTO Claims (ItemID, ClaimedBy, ClaimDate, ClaimDetails) VALUES (%s, %s, CURDATE(), %s)" # Menggunakan CURDATE() untuk tanggal saja
        cursor.execute(sql_claim, (item_id, claimed_by_user_id, claim_details))
        claim_id = cursor.lastrowid # Ambil ClaimID yang baru dibuat
        print(f"Claim inserted with ClaimID: {claim_id}") # Debugging print


        # 2. Masukkan URL gambar bukti ke tabel ClaimImages
        if claim_id and proof_image_urls:
            sql_image = "INSERT INTO ClaimImages (ClaimID, ImageURL) VALUES (%s, %s)"
            image_values = [(claim_id, url) for url in proof_image_urls]
            cursor.executemany(sql_image, image_values)
            print(f"Inserted {len(proof_image_urls)} proof image URLs for ClaimID {claim_id}.") # Debugging print


        conn.commit()
        print(f"New claim (ClaimID: {claim_id}) and proof images added successfully.") # Debugging print
        return claim_id # Kembalikan ClaimID yang baru dibuat

    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error
        print(f"Database Error in add_claim: {err}") # Log error
        return None
    except Exception as e:
        conn.rollback()
        print(f"An unexpected error occurred in add_claim: {e}") # Log error tak terduga
        return None
    finally:
        cursor.close()
        close_db_connection(conn)

def get_claims_by_user_id(user_id):
    """
    Mengambil daftar klaim yang diajukan oleh pengguna tertentu.
    Mengembalikan list of dictionaries klaim jika ditemukan, list kosong jika tidak atau error.
    """
    print(f"Attempting to fetch claims for UserID: {user_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi

    cursor = conn.cursor(dictionary=True) # Mengembalikan hasil sebagai dictionary
    claims_list = []

    try:
        # Query untuk mengambil klaim berdasarkan UserID pengklaim
        # Join dengan tabel Items untuk mendapatkan nama barang yang diklaim
        # Anda mungkin ingin join juga ke ItemImages untuk gambar item, atau ClaimImages untuk gambar bukti
        sql = """
            SELECT
                C.ClaimID,
                C.ItemID,
                I.ItemName, -- Ambil nama barang dari tabel Items
                C.ClaimDate,
                C.ClaimDetails, -- Ambil detail klaim
                C.VerificationStatus
            FROM
                Claims C
            JOIN
                Items I ON C.ItemID = I.ItemID -- Join dengan Items untuk nama barang
            WHERE
                C.ClaimedBy = %s
            ORDER BY
                C.ClaimDate DESC -- Urutkan berdasarkan tanggal klaim terbaru
        """
        cursor.execute(sql, (user_id,))
        claims_list = cursor.fetchall() # Ambil semua baris hasil

        print(f"Found {len(claims_list)} claims for UserID {user_id}.") # Debugging print
        return claims_list

    except mysql.connector.Error as err:
        print(f"Database Error in get_claims_by_user_id: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)

def get_pending_claims():
    """
    Mengambil daftar semua klaim dengan status 'Pending'.
    Mengembalikan list of dictionaries klaim jika ditemukan, list kosong jika tidak atau error.
    """
    print("Attempting to fetch all 'Pending' claims from DB for admin review...") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi

    cursor = conn.cursor(dictionary=True) # Mengembalikan hasil sebagai dictionary
    claims_list = []

    try:
        # Query untuk mengambil klaim dengan status 'Pending'
        # Join dengan Items dan Users/CampusUsers untuk mendapatkan detail barang dan pengklaim
        sql = """
            SELECT
                C.ClaimID,
                C.ItemID,
                I.ItemName,
                I.Description AS ItemDescription, -- Deskripsi barang
                I.Location AS ItemLocation, -- Lokasi penemuan barang
                C.ClaimedBy,
                CU.FullName AS ClaimedByFullName, -- Nama lengkap pengklaim
                U.Username AS ClaimedByUsername, -- Username pengklaim
                C.ClaimDate,
                C.ClaimDetails, -- Detail klaim
                C.VerificationStatus
            FROM
                Claims C
            JOIN
                Items I ON C.ItemID = I.ItemID
            JOIN -- Join dengan Users dan CampusUsers untuk info pengklaim
                Users U ON C.ClaimedBy = U.UserID
            JOIN
                CampusUsers CU ON U.CampusUserID = CU.CampusUserID
            WHERE
                C.VerificationStatus = 'Pending'
            ORDER BY
                C.ClaimDate ASC -- Urutkan berdasarkan tanggal klaim terlama (untuk diproses duluan)
        """
        cursor.execute(sql)
        claims_list = cursor.fetchall() # Ambil semua baris hasil

        print(f"Found {len(claims_list)} 'Pending' claims.") # Debugging print
        return claims_list

    except mysql.connector.Error as err:
        print(f"Database Error in get_pending_claims: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)

def get_claim_images_by_claim_id(claim_id):
    """
    Mengambil daftar URL gambar bukti untuk klaim tertentu.
    Mengembalikan list of strings (URL gambar) jika ditemukan, list kosong jika tidak atau error.
    """
    print(f"Attempting to fetch claim images for ClaimID: {claim_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi

    cursor = conn.cursor() # Tidak perlu dictionary=True jika hanya mengambil satu kolom
    image_urls = []

    try:
        # Query untuk mengambil semua ImageURL dari tabel ClaimImages untuk ClaimID tertentu
        sql = "SELECT ImageURL FROM ClaimImages WHERE ClaimID = %s"
        cursor.execute(sql, (claim_id,))
        results = cursor.fetchall() # Ambil semua baris hasil

        # Ekstrak URL dari hasil query (hasilnya adalah list of tuples, misal: [('url1',), ('url2',)])
        image_urls = [row[0] for row in results]

        print(f"Found {len(image_urls)} claim images for ClaimID {claim_id}.") # Debugging print
        return image_urls

    except mysql.connector.Error as err:
        print(f"Database Error in get_claim_images_by_claim_id: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)


def update_claim_status(claim_id, new_status):
    """
    Memperbarui status verifikasi klaim di tabel Claims.

    Args:
        claim_id (int): ClaimID dari klaim yang akan diperbarui.
        new_status (str): Status baru ('Approved' atau 'Rejected').

    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    print(f"Attempting to update status for ClaimID {claim_id} to '{new_status}'") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        # Pastikan new_status adalah nilai yang valid untuk ENUM
        if new_status not in ['Approved', 'Rejected']:
            print(f"Invalid status '{new_status}' for claim update.")
            return False

        sql = "UPDATE Claims SET VerificationStatus = %s WHERE ClaimID = %s"
        cursor.execute(sql, (new_status, claim_id))
        conn.commit()
        success = True
        print(f"ClaimID {claim_id} status updated to '{new_status}'.")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in update_claim_status: {err}") # Log error
        success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

# TODO: Tambahkan fungsi DAO lain untuk Claims (misal: get_claims_by_item)
# def get_claims_by_item(item_id):
#    ... logika SELECT klaim berdasarkan ItemID ...
#    pass


# --- Test Block (Opsional) ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan claim_dao.py langsung
    print("Testing claim_dao functions...")

    # Pastikan Anda memiliki koneksi database yang berfungsi dan tabel Claims/ClaimImages
    # Pastikan ada user dengan UserID 1 dan item dengan ItemID 1 di database Anda
    # Pastikan ada beberapa klaim dengan status 'Pending' untuk pengujian get_pending_claims
    # Pastikan ada klaim dengan gambar bukti untuk pengujian get_claim_images_by_claim_id

    # --- Test add_claim ---
    # print("\n--- Testing add_claim ---")
    # test_item_id = 1 # Ganti dengan ItemID yang ada di DB
    # test_claimed_by_user_id = 1 # Ganti dengan UserID yang ada di DB
    # test_claim_details = "Saya kehilangan dompet ini kemarin di lokasi tersebut. Ada kartu mahasiswa di dalamnya."
    # # URL gambar bukti dummy (ganti dengan URL asli jika Anda mengunggah bukti)
    # test_proof_image_urls = [
    #     "https://ik.imagekit.io/ilsoqlnic/dummy_proof_1.jpg",
    #     "https://ik.imagekit.io/ilsoqlnic/dummy_proof_2.jpg"
    #     ] # Ganti dengan URL gambar bukti asli jika ada

    # print(f"Attempting to add claim for ItemID {test_item_id} by UserID {test_claimed_by_user_id}...")
    # new_claim_id = add_claim(test_item_id, test_claimed_by_user_id, test_claim_details, test_proof_image_urls)

    # if new_claim_id:
    #     print(f"Claim added successfully with ClaimID: {new_claim_id}")
    #     # Anda bisa cek database secara manual untuk memverifikasi data
    # else:
    #     print("Failed to add claim.")

    # --- Test get_claims_by_user_id ---
    # print(f"\n--- Testing get_claims_by_user_id for UserID {test_claimed_by_user_id} ---")
    # user_claims = get_claims_by_user_id(test_claimed_by_user_id)

    # if user_claims:
    #     print(f"Successfully fetched {len(user_claims)} claims for UserID {test_claimed_by_user_id}:")
    #     for claim in user_claims:
    #         print(f"  ClaimID: {claim.get('ClaimID')}, Item: {claim.get('ItemName')}, Date: {claim.get('ClaimDate')}, Status: {claim.get('VerificationStatus')}")
    # else:
    #     print(f"No claims found for UserID {test_claimed_by_user_id} or failed to fetch.")

    # --- Test get_pending_claims ---
    print("\n--- Testing get_pending_claims ---")
    pending_claims = get_pending_claims()

    if pending_claims:
        print(f"Successfully fetched {len(pending_claims)} pending claims:")
        for claim in pending_claims:
            print(f"  ClaimID: {claim.get('ClaimID')}, Item: {claim.get('ItemName')}, ClaimedBy: {claim.get('ClaimedByFullName')}, Date: {claim.get('ClaimDate')}, Status: {claim.get('VerificationStatus')}")
            print(f"    Details: {claim.get('ClaimDetails')}")
            # Anda bisa tambahkan logika untuk mengambil gambar bukti di sini jika perlu
    else:
        print("No 'Pending' claims found or failed to fetch.")

    # --- Test get_claim_images_by_claim_id ---
    # Ganti dengan ClaimID yang ada di database Anda dan memiliki gambar bukti
    test_claim_id_with_images = 1 # Ganti dengan ClaimID yang valid
    print(f"\n--- Testing get_claim_images_by_claim_id for ClaimID {test_claim_id_with_images} ---")
    claim_images = get_claim_images_by_claim_id(test_claim_id_with_images)

    if claim_images:
        print(f"Successfully fetched {len(claim_images)} images for ClaimID {test_claim_id_with_images}:")
        for url in claim_images:
            print(f"  Image URL: {url}")
    else:
        print(f"No images found for ClaimID {test_claim_id_with_images} or failed to fetch.")



# src/database/claim_dao.py

import mysql.connector
import datetime
# Mengimpor fungsi koneksi database dari db_connector
from src.database.db_connector import create_db_connection, close_db_connection
# Mengimpor fungsi untuk update item status dari item_dao
# Kita akan tambahkan atau pastikan fungsi ini ada di item_dao.py nanti
from src.database.item_dao import update_item_status # Asumsi fungsi ini ada/akan ada
# Mengimpor fungsi add_notification dari notification_dao
from src.database.notification_dao import add_notification # Impor fungsi add_notification

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

def update_claim_status(claim_id, new_status):
    """
    Memperbarui status verifikasi klaim di tabel Claims.
    Mengirim notifikasi ke pengguna yang mengajukan klaim.
    Jika status disetujui ('Approved'), juga perbarui status item terkait menjadi 'Claimed'
    dan set IsActive item menjadi FALSE.

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

    cursor = conn.cursor(dictionary=True) # Gunakan dictionary=True untuk mengambil data klaim
    success = False
    claimed_by_user_id = None
    item_id = None
    item_name = None

    try:
        conn.start_transaction() # Mulai transaksi

        # 1. Ambil data klaim (terutama ClaimedBy dan ItemID) SEBELUM diupdate
        sql_get_claim_info = """
            SELECT
                C.ClaimedBy,
                C.ItemID,
                I.ItemName -- Ambil nama barang untuk notifikasi
            FROM
                Claims C
            JOIN
                Items I ON C.ItemID = I.ItemID
            WHERE
                C.ClaimID = %s
        """
        cursor.execute(sql_get_claim_info, (claim_id,))
        claim_info = cursor.fetchone()

        if claim_info:
            claimed_by_user_id = claim_info['ClaimedBy']
            item_id = claim_info['ItemID']
            item_name = claim_info['ItemName']
            print(f"Claim info found: ClaimedBy={claimed_by_user_id}, ItemID={item_id}, ItemName='{item_name}'") # Debugging print
        else:
            print(f"ClaimID {claim_id} not found for status update.")
            conn.rollback() # Rollback karena klaim tidak ditemukan
            return False # Gagal karena klaim tidak ada


        # 2. Perbarui status verifikasi klaim di tabel Claims
        # Pastikan new_status adalah nilai yang valid untuk ENUM
        if new_status not in ['Approved', 'Rejected']:
            print(f"Invalid status '{new_status}' for claim update.")
            conn.rollback() # Rollback karena status tidak valid
            return False

        sql_update_claim = "UPDATE Claims SET VerificationStatus = %s WHERE ClaimID = %s"
        cursor.execute(sql_update_claim, (new_status, claim_id))
        print(f"ClaimID {claim_id} status updated to '{new_status}'.") # Debugging print


        # 3. Jika status disetujui, perbarui status item terkait
        if new_status == 'Approved' and item_id is not None:
            print(f"Claim Approved. Attempting to update ItemID {item_id} status to 'Claimed'...") # Debugging print
            # Panggil fungsi update_item_status dari item_dao
            # Fungsi ini juga akan set IsActive item menjadi FALSE
            item_update_success = update_item_status(item_id, 'Claimed')
            if item_update_success:
                print(f"ItemID {item_id} status successfully updated to 'Claimed'.") # Debugging print
            else:
                print(f"Failed to update ItemID {item_id} status to 'Claimed'.") # Debugging print
                # Anda bisa memilih untuk membatalkan seluruh transaksi di sini
                # atau melanjutkan tapi log errornya. Kita log error dan lanjutkan.


        # 4. Kirim notifikasi ke pengguna yang mengajukan klaim
        if claimed_by_user_id is not None:
            notification_message = f"Status klaim Anda untuk barang '{item_name}' telah diperbarui menjadi '{new_status}'."
            print(f"Attempting to send notification to UserID {claimed_by_user_id}: '{notification_message}'") # Debugging print
            # Panggil fungsi add_notification dari notification_dao
            notification_id = add_notification(claimed_by_user_id, notification_message)
            if notification_id:
                print(f"Notification sent successfully with ID: {notification_id}") # Debugging print
            else:
                print("Failed to send notification.") # Debugging print
                # Log error, tapi jangan batalkan transaksi utama hanya karena notifikasi gagal


        # Commit transaksi jika semua operasi database berhasil
        conn.commit()
        success = True
        print(f"ClaimID {claim_id} status update process completed successfully.") # Debugging print


    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error database
        print(f"Database Error in update_claim_status: {err}") # Log error
        success = False
    except Exception as e:
        conn.rollback()
        print(f"An unexpected error occurred in update_claim_status: {e}") # Log error tak terduga
        success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

# --- Fungsi Baru: get_claim_images_by_claim_id ---
def get_claim_images_by_claim_id(claim_id):
    """
    Mengambil daftar semua URL gambar bukti untuk klaim tertentu berdasarkan ClaimID.
    Mengembalikan list of strings (URL gambar), atau list kosong jika tidak ada gambar atau error.
    """
    print(f"Attempting to fetch all proof image URLs for ClaimID: {claim_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi

    cursor = conn.cursor() # Tidak perlu dictionary=True karena hanya mengambil satu kolom
    image_urls_list = []

    try:
        # Query untuk mengambil semua ImageURL berdasarkan ClaimID dari tabel ClaimImages
        sql = "SELECT ImageURL FROM ClaimImages WHERE ClaimID = %s"
        cursor.execute(sql, (claim_id,))
        # fetchall() akan mengembalikan list of tuples, ambil elemen pertama dari setiap tuple
        image_urls_list = [row[0] for row in cursor.fetchall()]

        print(f"Found {len(image_urls_list)} proof image URLs for ClaimID {claim_id}.") # Debugging print
        return image_urls_list

    except mysql.connector.Error as err:
        print(f"Database Error in get_claim_images_by_claim_id: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)


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

    # --- Test update_claim_status ---
    # Asumsi ada klaim dengan ClaimID 1 yang statusnya 'Pending'
    # test_claim_id_to_update = 1 # Ganti dengan ClaimID yang ada dan statusnya 'Pending'
    # print(f"\n--- Testing update_claim_status for ClaimID {test_claim_id_to_update} ---")
    # # Coba update status menjadi 'Approved'
    # update_success = update_claim_status(test_claim_id_to_update, 'Approved')
    # if update_success:
    #     print(f"Status update for ClaimID {test_claim_id_to_update} successful.")
    # else:
    #     print(f"Status update for ClaimID {test_claim_id_to_update} failed.")

    # # Coba update status menjadi 'Rejected'
    # # update_success = update_claim_status(test_claim_id_to_update, 'Rejected')
    # # if update_success:
    # #     print(f"Status update for ClaimID {test_claim_id_to_update} successful.")
    # # else:
    # #     print(f"Status update for ClaimID {test_claim_id_to_update} failed.")


    # --- Test get_claim_images_by_claim_id ---
    # Asumsi ada klaim dengan ClaimID yang memiliki gambar bukti di database
    # Ganti 1 dengan ClaimID yang pasti punya gambar bukti di DB Anda
    test_claim_id_with_images = 1 # <--- GANTI DENGAN CLAIMID YANG PUNYA GAMBAR BUKTI
    print(f"\n--- Testing get_claim_images_by_claim_id for ClaimID {test_claim_id_with_images} ---")
    claim_image_urls = get_claim_images_by_claim_id(test_claim_id_with_images)

    if claim_image_urls:
        print(f"Successfully fetched {len(claim_image_urls)} proof image URLs for ClaimID {test_claim_id_with_images}:")
        for url in claim_image_urls:
            print(f"  - {url}")
    else:
        print(f"No proof image URLs found for ClaimID {test_claim_id_with_images} or failed to fetch.")


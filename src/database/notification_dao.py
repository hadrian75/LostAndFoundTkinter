# src/database/notification_dao.py

import mysql.connector
import datetime
# Mengimpor fungsi koneksi database dari db_connector
from src.database.db_connector import create_db_connection, close_db_connection

def get_notifications_by_user(user_id, include_read=True):
    """
    Mengambil daftar notifikasi untuk pengguna tertentu dari database.

    Args:
        user_id (int): UserID dari pengguna penerima notifikasi.
        include_read (bool): Jika True, sertakan notifikasi yang sudah dibaca.
                             Jika False, hanya ambil notifikasi yang belum dibaca.

    Returns:
        list: List of dictionaries, di mana setiap dictionary merepresentasikan satu notifikasi.
              Mengembalikan list kosong jika tidak ada notifikasi atau jika terjadi error.
    """
    print(f"Attempting to fetch notifications for UserID: {user_id}, Include Read: {include_read}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return [] # Gagal koneksi, kembalikan list kosong

    # Menggunakan dictionary=True agar hasil query mudah diakses dengan nama kolom
    cursor = conn.cursor(dictionary=True)
    notifications_list = []

    try:
        # Query dasar untuk mengambil notifikasi berdasarkan ReceiverID
        sql = """
            SELECT
                NotificationID,
                ReceiverID,
                Message,
                SentAt,
                IsRead
            FROM
                Notification
            WHERE
                ReceiverID = %s
        """
        params = (user_id,)

        # Tambahkan kondisi WHERE jika hanya ingin notifikasi yang belum dibaca
        if not include_read:
            sql += " AND IsRead = FALSE"

        # Urutkan berdasarkan waktu pengiriman terbaru
        sql += " ORDER BY SentAt DESC"

        cursor.execute(sql, params)
        notifications_list = cursor.fetchall() # Ambil semua baris hasil

        print(f"Found {len(notifications_list)} notifications for UserID {user_id}.") # Debugging print
        return notifications_list

    except mysql.connector.Error as err:
        print(f"Database Error in get_notifications_by_user: {err}") # Log error
        return [] # Kembalikan list kosong jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)

def mark_notification_as_read(notification_id):
    """
    Menandai notifikasi tertentu sebagai sudah dibaca di database.

    Args:
        notification_id (int): NotificationID dari notifikasi yang akan ditandai.

    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    print(f"Attempting to mark notification ID {notification_id} as read.") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return False # Gagal koneksi

    cursor = conn.cursor()
    success = False

    try:
        # Query untuk mengupdate status IsRead menjadi TRUE
        sql = """
            UPDATE Notification
            SET IsRead = TRUE
            WHERE NotificationID = %s AND IsRead = FALSE -- Hanya update jika statusnya masih FALSE
        """
        cursor.execute(sql, (notification_id,))
        conn.commit()

        # Periksa apakah ada baris yang terpengaruh (berarti notifikasi ditemukan dan statusnya diubah)
        if cursor.rowcount > 0:
            success = True
            print(f"Notification ID {notification_id} marked as read successfully.") # Debugging print
        else:
            # Notifikasi tidak ditemukan atau statusnya sudah TRUE
            print(f"Notification ID {notification_id} not found or already marked as read.") # Debugging print
            success = True # Dianggap berhasil jika sudah dibaca

    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error
        print(f"Database Error in mark_notification_as_read: {err}") # Log error
        success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

def add_notification(receiver_id, message):
    """
    Menambahkan notifikasi baru ke database.

    Args:
        receiver_id (int): UserID dari pengguna yang akan menerima notifikasi.
        message (str): Isi pesan notifikasi.

    Returns:
        int: NotificationID dari notifikasi yang baru ditambahkan jika berhasil,
             None jika gagal.
    """
    print(f"Attempting to add notification for ReceiverID: {receiver_id} with message: '{message[:50]}...'") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return None # Gagal koneksi

    cursor = conn.cursor()
    notification_id = None

    try:
        # Query untuk memasukkan notifikasi baru
        # SentAt akan otomatis menggunakan CURRENT_TIMESTAMP
        # IsRead default FALSE
        sql = """
            INSERT INTO Notification (ReceiverID, Message)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (receiver_id, message))
        conn.commit()
        notification_id = cursor.lastrowid # Ambil ID yang baru dibuat

        print(f"Notification added successfully with NotificationID: {notification_id}") # Debugging print
        return notification_id

    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error
        print(f"Database Error in add_notification: {err}") # Log error
        return None
    except Exception as e:
        conn.rollback()
        print(f"An unexpected error occurred in add_notification: {e}") # Log error tak terduga
        return None
    finally:
        cursor.close()
        close_db_connection(conn)

# --- Fungsi Baru: get_unread_notifications_count ---
def get_unread_notifications_count(user_id):
    """
    Mengambil jumlah notifikasi yang belum dibaca untuk pengguna tertentu.

    Args:
        user_id (int): UserID dari pengguna penerima notifikasi.

    Returns:
        int: Jumlah notifikasi yang belum dibaca, atau 0 jika terjadi error.
    """
    print(f"Attempting to fetch unread notifications count for UserID: {user_id}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return 0 # Gagal koneksi, kembalikan 0

    cursor = conn.cursor() # Tidak perlu dictionary=True karena hanya mengambil satu nilai
    count = 0

    try:
        # Query untuk menghitung baris dengan ReceiverID dan IsRead = FALSE
        sql = """
            SELECT
                COUNT(*)
            FROM
                Notification
            WHERE
                ReceiverID = %s AND IsRead = FALSE
        """
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone() # Ambil satu baris hasil (tuple)

        if result and result[0] is not None:
            count = int(result[0]) # Ambil nilai count dari tuple
        else:
             count = 0 # Jika hasil query kosong atau nilai pertama None

        print(f"Found {count} unread notifications for UserID {user_id}.") # Debugging print
        return count

    except mysql.connector.Error as err:
        print(f"Database Error in get_unread_notifications_count: {err}") # Log error
        return 0 # Kembalikan 0 jika terjadi error
    finally:
        cursor.close()
        close_db_connection(conn)


# TODO: Tambahkan fungsi DAO lain untuk Notifikasi (misal: delete_notification)
# def delete_notification(notification_id):
#    ... logika DELETE notifikasi ...
#    pass

# --- Test Block (Opsional) ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan notification_dao.py langsung
    print("Testing notification_dao functions...")

    # Pastikan Anda memiliki koneksi database yang berfungsi dan tabel Notification
    # dengan beberapa data dummy.
    # Pastikan ada user dengan UserID 1 di tabel Users untuk ReceiverID

    # --- Test get_notifications_by_user ---
    print("\n--- Testing get_notifications_by_user ---")
    test_user_id = 1 # Ganti dengan UserID yang ada di database Anda
    print(f"Fetching all notifications for UserID {test_user_id} (including read)...")
    notifications_all = get_notifications_by_user(test_user_id, include_read=True)
    if notifications_all:
        print(f"Found {len(notifications_all)} notifications (including read):")
        for notif in notifications_all:
            print(f"  ID: {notif.get('NotificationID')}, Message: {notif.get('Message')[:50]}..., Read: {notif.get('IsRead')}")
    else:
        print(f"No notifications found for UserID {test_user_id} (including read).")

    print(f"\nFetching unread notifications for UserID {test_user_id}...")
    notifications_unread = get_notifications_by_user(test_user_id, include_read=False)
    if notifications_unread:
        print(f"Found {len(notifications_unread)} unread notifications:")
        for notif in notifications_unread:
            print(f"  ID: {notif.get('NotificationID')}, Message: {notif.get('Message')[:50]}..., Read: {notif.get('IsRead')}")
    else:
        print(f"No unread notifications found for UserID {test_user_id}.")


    # --- Test mark_notification_as_read ---
    print("\n--- Testing mark_notification_as_read ---")
    # Cari NotificationID yang statusnya IsRead = FALSE di database Anda
    # Ganti dengan NotificationID yang valid untuk diuji
    test_notification_id_to_mark = None # <--- GANTI dengan ID notifikasi yang BELUM dibaca

    # Ambil ID notifikasi pertama yang belum dibaca dari hasil sebelumnya jika ada
    if notifications_unread:
        test_notification_id_to_mark = notifications_unread[0].get('NotificationID')
        print(f"Attempting to mark Notification ID {test_notification_id_to_mark} as read...")
        mark_success = mark_notification_as_read(test_notification_id_to_mark)

        if mark_success:
            print(f"Marking Notification ID {test_notification_id_to_mark} as read successful.")
            # Cek kembali notifikasi yang belum dibaca untuk UserID yang sama
            print(f"\nRe-fetching unread notifications for UserID {test_user_id} after marking one as read...")
            notifications_unread_after_mark = get_notifications_by_user(test_user_id, include_read=False)
            if notifications_unread_after_mark:
                 print(f"Found {len(notifications_unread_after_mark)} unread notifications:")
                 for notif in notifications_unread_after_mark:
                      print(f"  ID: {notif.get('NotificationID')}, Message: {notif.get('Message')[:50]}..., Read: {notif.get('IsRead')}")
            else:
                 print(f"No unread notifications found for UserID {test_user_id} after marking one as read.")
        else:
            print(f"Failed to mark Notification ID {test_notification_id_to_mark} as read.")

    else:
        print("Skipping mark_notification_as_read test as no unread notifications were found.")

    # --- Test add_notification ---
    print("\n--- Testing add_notification ---")
    test_receiver_id = 1 # Ganti dengan UserID penerima yang valid
    test_message = "Ini adalah notifikasi uji dari fungsi add_notification."
    print(f"Attempting to add notification for UserID {test_receiver_id}...")
    new_notif_id = add_notification(test_receiver_id, test_message)

    if new_notif_id:
        print(f"New notification added successfully with ID: {new_notif_id}")
        # Anda bisa cek database secara manual untuk memverifikasi data
    else:
        print("Failed to add new notification.")

    # --- Test get_unread_notifications_count ---
    print("\n--- Testing get_unread_notifications_count ---")
    test_user_id_count = 1 # Ganti dengan UserID yang ada di database Anda
    print(f"Fetching unread count for UserID {test_user_id_count}...")
    unread_count = get_unread_notifications_count(test_user_id_count)
    print(f"Unread count for UserID {test_user_id_count}: {unread_count}")


# src/database/auth_dao.py

import mysql.connector
import datetime
import random
import os
# Mengimpor fungsi koneksi database dari db_connector
from src.database.db_connector import create_db_connection, close_db_connection
# Mengimpor fungsi hashing dan check password dari auth_utils
from src.utils.auth_utils import check_password, hash_password # Impor hash_password juga
# Mengimpor fungsi send_email dari email_utils (akan dipanggil dari GUI/Service layer)
# from src.utils.email_utils import send_email # Email sending should ideally be outside DAO

def create_new_user_with_token(full_name, nim_nip, email, role_id, username, password_hash, token, expiry_time):
    """
    Menyimpan data pengguna baru ke tabel CampusUsers dan Users,
    serta membuat token verifikasi email.
    Mengembalikan UserID yang baru dibuat jika berhasil, None jika gagal.
    """
    conn = create_db_connection()
    if conn is None:
        return None, None # Gagal koneksi

    cursor = conn.cursor()
    user_id = None # Inisialisasi user_id

    try:
        # Mulai transaksi untuk memastikan kedua operasi INSERT berhasil atau tidak sama sekali
        conn.start_transaction()

        # 1. Masukkan data ke tabel CampusUsers
        sql_campus = "INSERT INTO CampusUsers (RoleID, FullName, NIM_NIP, Email) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_campus, (role_id, full_name, nim_nip, email))
        campus_user_id = cursor.lastrowid # Ambil ID yang baru dibuat

        # 2. Masukkan data ke tabel Users
        # IsActive diset FALSE secara default, akan diaktifkan setelah verifikasi email
        # IsAdmin diset FALSE secara default untuk pendaftar baru
        sql_user = "INSERT INTO Users (CampusUserID, Username, PasswordHash, IsActive, IsAdmin) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_user, (campus_user_id, username, password_hash, False, False))
        user_id = cursor.lastrowid # Ambil UserID yang baru dibuat

        # 3. Masukkan token verifikasi email ke tabel EmailVerificationToken
        sql_token = "INSERT INTO EmailVerificationToken (UserID, Token, ExpiryTime) VALUES (%s, %s, %s)"
        cursor.execute(sql_token, (user_id, token, expiry_time))

        # Commit transaksi jika semua operasi berhasil
        conn.commit()
        return user_id, token # Kembalikan UserID dan Token untuk langkah verifikasi

    except mysql.connector.Error as err:
        # Rollback transaksi jika terjadi error
        conn.rollback()
        print(f"Database Error in create_new_user_with_token: {err}") # Log error ke konsol
        # Anda bisa menambahkan logika untuk menampilkan error di GUI di layer GUI
        return None, None
    finally:
        cursor.close()
        close_db_connection(conn)


def authenticate_user(username, plain_password):
    """
    Memverifikasi kredensial login pengguna.
    Mengambil password hash dari database dan membandingkannya dengan input password (plain text) menggunakan bcrypt.
    Mengembalikan dictionary data pengguna (UserID, IsActive, IsAdmin) jika berhasil dan aktif,
    None jika gagal autentikasi atau akun tidak aktif.
    """
    print(f"Attempting to authenticate user: {username}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True) # Mengembalikan hasil sebagai dictionary
    user_data = None

    try:
        # Langkah 1: Ambil data pengguna (termasuk password hash dan status aktif) berdasarkan username
        # JANGAN bandingkan password di sini di SQL
        sql_fetch_user = "SELECT UserID, PasswordHash, IsActive, IsAdmin FROM Users WHERE Username = %s"
        cursor.execute(sql_fetch_user, (username,)) # Perhatikan koma setelah username untuk tuple

        user = cursor.fetchone() # Ambil satu baris hasil

        if user:
            print(f"User '{username}' found in DB.") # Debugging print
            stored_password_hash = user['PasswordHash']
            is_active = user['IsActive']
            user_id = user['UserID']
            is_admin = user['IsAdmin']

            print(f"Stored Password Hash: {stored_password_hash}") # Debugging print
            print(f"Input Password (plain text from GUI): {plain_password}") # Debugging print

            # Langkah 2: Verifikasi password menggunakan bcrypt.checkpw
            # check_password membandingkan password plain text dengan hash bcrypt
            is_password_correct = check_password(plain_password, stored_password_hash)

            print(f"Password check result (using check_password): {is_password_correct}") # Debugging print
            print(f"Is account active? {is_active}") # Debugging print


            if is_password_correct:
                if is_active:
                    user_data = {'UserID': user_id, 'IsActive': is_active, 'IsAdmin': is_admin} # Login berhasil dan akun aktif
                    print("Authentication successful and account is active.") # Debugging print
                else:
                    # Akun ditemukan dan password benar, tapi tidak aktif (misal: belum verifikasi email)
                    print(f"Authentication successful, but user '{username}' is not active.") # Debugging print
                    # Kembalikan data dengan IsActive=False agar GUI bisa menampilkan pesan "Akun belum aktif"
                    user_data = {'UserID': user_id, 'IsActive': is_active, 'IsAdmin': is_admin}
            else:
                # Password tidak cocok
                print(f"Authentication failed: Invalid password for username '{username}'.") # Debugging print
                user_data = None # Kredensial salah

        else:
            # Username tidak ditemukan
            print(f"Authentication failed: Username '{username}' not found.") # Debugging print
            user_data = None

    except mysql.connector.Error as err:
        print(f"Database Error in authenticate_user: {err}") # Log error
        user_data = None
    finally:
        cursor.close()
        close_db_connection(conn)
        return user_data


def activate_user_account(user_id):
    """
    Mengaktifkan akun pengguna dengan mengubah status IsActive menjadi TRUE.
    Mengembalikan True jika berhasil, False jika gagal.
    """
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        sql = "UPDATE Users SET IsActive = TRUE WHERE UserID = %s"
        cursor.execute(sql, (user_id,))
        conn.commit()
        success = True
        print(f"User account with UserID {user_id} activated successfully.")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in activate_user_account: {err}") # Log error
        success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

def verify_email_token(user_id, token):
    """
    Memverifikasi token email dan mengaktifkan akun pengguna jika valid.
    Mengembalikan True jika verifikasi berhasil, False jika gagal.
    """
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    verification_success = False

    try:
        conn.start_transaction()

        # Cari token yang cocok untuk UserID dan Token yang diberikan, belum digunakan, dan belum kedaluwarsa
        sql_find_token = "SELECT TokenID, ExpiryTime, IsUsed FROM EmailVerificationToken WHERE UserID = %s AND Token = %s"
        cursor.execute(sql_find_token, (user_id, token))
        token_data = cursor.fetchone()

        if token_data:
            token_id, expiry_time, is_used = token_data

            if is_used:
                print(f"Verification failed for UserID {user_id}: Token already used.")
                # messagebox.showwarning("Verifikasi Gagal", "Token sudah digunakan.") # Opsional: Tampilkan di GUI
                conn.rollback()
                return False

            # Perbandingan waktu kedaluwatan
            if expiry_time < datetime.datetime.now():
                print(f"Verification failed for UserID {user_id}: Token expired.")
                # messagebox.showwarning("Verifikasi Gagal", "Token sudah kedaluwarsa.") # Opsional: Tampilkan di GUI
                conn.rollback()
                return False

            # Token valid, aktifkan akun pengguna
            sql_activate_user = "UPDATE Users SET IsActive = TRUE WHERE UserID = %s"
            cursor.execute(sql_activate_user, (user_id,))

            # Tandai token sebagai sudah digunakan
            sql_mark_used = "UPDATE EmailVerificationToken SET IsUsed = TRUE WHERE TokenID = %s"
            cursor.execute(sql_mark_used, (token_id,))

            conn.commit()
            verification_success = True # Verifikasi berhasil
            print(f"Email verification successful for UserID {user_id}. Account activated.")

        else:
            # Token tidak ditemukan atau tidak cocok
            print(f"Verification failed: Invalid token '{token}' for UserID {user_id}.")
            # messagebox.showwarning("Verifikasi Gagal", "Kode OTP tidak valid.") # Opsional: Tampilkan di GUI
            conn.rollback()
            verification_success = False

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in verify_email_token: {err}") # Log error
        verification_success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return verification_success

def request_password_reset(username_or_email):
    """
    Memproses permintaan reset password.
    Mencari pengguna berdasarkan username atau email, membuat token, dan menyimpannya di DB.
    Mengembalikan UserID, Token, dan Email pengguna jika berhasil, None jika gagal.
    """
    print(f"Processing password reset request for: {username_or_email}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return None, None, None # Gagal koneksi

    cursor = conn.cursor(dictionary=True)
    user_info = None # Untuk menyimpan UserID dan Email

    try:
        # Langkah 1: Cari pengguna berdasarkan username atau email
        # Join dengan CampusUsers untuk mendapatkan Email
        sql_find_user = """
            SELECT
                U.UserID,
                CU.Email
            FROM
                Users U
            JOIN
                CampusUsers CU ON U.CampusUserID = CU.CampusUserID
            WHERE
                U.Username = %s OR CU.Email = %s
        """
        cursor.execute(sql_find_user, (username_or_email, username_or_email))
        user = cursor.fetchone()

        if user:
            user_id = user['UserID']
            user_email = user['Email']
            print(f"User found for reset: UserID={user_id}, Email={user_email}") # Debugging print

            # Langkah 2: Hasilkan token reset password (bisa string acak yang lebih panjang)
            # Menggunakan kombinasi random bytes dan heksadesimal untuk token yang lebih kuat dari OTP
            token_bytes = os.urandom(32) # 32 bytes = 256 bits
            reset_token = token_bytes.hex() # Konversi ke string heksadesimal

            # Langkah 3: Hitung waktu kedaluwarsa token (misal: 30 menit)
            # Anda bisa ambil durasi dari config.py jika perlu
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
            print(f"Generated reset token: {reset_token}") # Debugging print
            print(f"Token expiry time: {expiry_time}") # Debugging print

            # Langkah 4: Simpan token di tabel PasswordResetToken
            # Asumsi tabel PasswordResetToken sudah ada (sesuai skema)
            sql_insert_token = """
                INSERT INTO PasswordResetToken (UserID, Token, ExpiryTime, IsUsed)
                VALUES (%s, %s, %s, %s)
            """
            # Set IsUsed = FALSE secara default saat token dibuat
            cursor.execute(sql_insert_token, (user_id, reset_token, expiry_time, False))
            conn.commit()
            print(f"Reset token saved for UserID {user_id}.") # Debugging print


            # Mengembalikan informasi yang diperlukan untuk mengirim email
            return user_id, reset_token, user_email

        else:
            # Pengguna tidak ditemukan
            print(f"Password reset failed: User '{username_or_email}' not found.") # Log error
            # Penting: Jangan beritahu pengguna apakah username/email tidak ada di GUI
            # Cukup beri pesan umum seperti "Jika terdaftar, email akan dikirim"
            return None, None, None # Pengguna tidak ditemukan

    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error database
        print(f"Database Error in request_password_reset: {err}") # Log error
        return None, None, None
    except Exception as e:
        print(f"An unexpected error occurred in request_password_reset: {e}") # Log error tak terduga
        return None, None, None
    finally:
        cursor.close()
        close_db_connection(conn)

def reset_password_with_token(token, new_plain_password):
    """
    Memverifikasi token reset password dan mengupdate password pengguna jika valid.
    Mengembalikan True jika reset berhasil, False jika gagal.
    """
    print(f"Attempting to reset password with token: {token}") # Debugging print
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    reset_success = False

    try:
        conn.start_transaction()

        # Langkah 1: Cari token di tabel PasswordResetToken
        sql_find_token = "SELECT TokenID, UserID, ExpiryTime, IsUsed FROM PasswordResetToken WHERE Token = %s"
        cursor.execute(sql_find_token, (token,))
        token_data = cursor.fetchone() # Menggunakan fetchone karena token harus unik

        if token_data:
            token_id, user_id, expiry_time, is_used = token_data

            if is_used:
                print(f"Reset failed for token '{token}': Token already used (TokenID: {token_id}).")
                conn.rollback()
                return False

            # Perbandingan waktu kedaluwarsa
            if expiry_time < datetime.datetime.now():
                print(f"Reset failed for token '{token}': Token expired (TokenID: {token_id}).")
                conn.rollback()
                return False

            # Token valid, hash password baru
            new_password_hash = hash_password(new_plain_password)
            print(f"New password hashed: {new_password_hash}") # Debugging print


            # Langkah 2: Update password pengguna di tabel Users
            sql_update_password = "UPDATE Users SET PasswordHash = %s WHERE UserID = %s"
            cursor.execute(sql_update_password, (new_password_hash, user_id))

            # Langkah 3: Tandai token sebagai sudah digunakan
            sql_mark_used = "UPDATE PasswordResetToken SET IsUsed = TRUE WHERE TokenID = %s"
            cursor.execute(sql_mark_used, (token_id,))

            conn.commit()
            reset_success = True # Reset berhasil
            print(f"Password reset successful for UserID {user_id} using token {token_id}.")

        else:
            # Token tidak ditemukan
            print(f"Reset failed: Invalid token '{token}'.") # Log error
            reset_success = False

    except mysql.connector.Error as err:
        conn.rollback() # Rollback jika terjadi error database
        print(f"Database Error in reset_password_with_token: {err}") # Log error
        reset_success = False
    except Exception as e:
        print(f"An unexpected error occurred in reset_password_with_token: {e}") # Log error tak terduga
        reset_success = False
    finally:
        cursor.close()
        close_db_connection(conn)
        return reset_success


# --- Test Block (Opsional) ---
# Anda bisa menambahkan blok __main__ di sini untuk menguji fungsi-fungsi DAO ini secara terpisah
# Pastikan Anda memiliki database dan tabel yang sudah dibuat sebelum menjalankan test ini.
# if __name__ == "__main__":
#     print("Testing auth_dao functions...")
#     from src.utils.auth_utils import hash_password # Pastikan auth_utils ada dan berfungsi
#     # Asumsi ada user dengan UserID 1 di database Anda
#     test_user_id = 1
#     test_username = "testuser" # Ganti dengan username user_id 1 jika berbeda
#     test_email = "test@example.com" # Ganti dengan email user_id 1 jika berbeda
#
#     # --- Test Request Password Reset ---
#     print("\n--- Testing Request Password Reset ---")
#     user_id_req, token_req, email_req = request_password_reset(test_username) # Coba pakai username
#     # user_id_req, token_req, email_req = request_password_reset(test_email) # Atau coba pakai email
#
#     if user_id_req and token_req and email_req:
#         print(f"Request successful: UserID={user_id_req}, Token={token_req}, Email={email_req}")
#         # SIMULASI pengiriman email di sini
#         print(f"Simulasi: Email reset password dikirim ke {email_req} dengan token {token_req}")
#
#         # --- Test Reset Password with Token ---
#         print("\n--- Testing Reset Password with Token ---")
#         # Tunggu beberapa detik jika perlu untuk simulasi
#         # import time
#         # time.sleep(2)
#
#         new_pass = "newpassword123"
#         print(f"Attempting to reset password for UserID {user_id_req} with token {token_req} and new password '{new_pass}'...")
#         reset_success = reset_password_with_token(token_req, new_pass)
#
#         if reset_success:
#             print("Reset password test successful!")
#             # Coba login dengan password baru
#             print(f"Attempting to login with {test_username} and new password '{new_pass}'...")
#             logged_in_user = authenticate_user(test_username, new_pass)
#             if logged_in_user:
#                 print(f"Login with new password successful: {logged_in_user}")
#             else:
#                 print("Login with new password failed.")
#         else:
#             print("Reset password test failed.")
#
#         # --- Test Reset Password with Used/Expired Token (akan gagal) ---
#         print("\n--- Testing Reset Password with Used/Expired Token ---")
#         # Coba lagi dengan token yang sama (seharusnya IsUsed=TRUE sekarang)
#         print(f"Attempting to reset password again with the same token {token_req}...")
#         reset_success_again = reset_password_with_token(token_req, "anothernewpass")
#         if not reset_success_again:
#             print("Testing reset with used token failed as expected.")
#         else:
#             print("Testing reset with used token unexpectedly succeeded.")
#
#     else:
#         print("Request password reset test failed.")


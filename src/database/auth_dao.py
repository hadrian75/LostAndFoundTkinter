# src/database/auth_dao.py

import mysql.connector
import datetime
import random
import os
from src.database.db_connector import create_db_connection, close_db_connection
from src.utils.auth_utils import check_password, hash_password

def _convert_user_id(user_id):
    """Helper function to safely convert user_id to integer"""
    if isinstance(user_id, tuple):
        if len(user_id) > 0:
            return int(user_id[0])
        raise ValueError("Empty tuple received for user_id")
    return int(user_id)

def create_new_user_with_token(full_name, nim_nip, email, role_id, username, password_hash, token, expiry_time):
    """Menyimpan data pengguna baru ke tabel CampusUsers dan Users."""
    conn = create_db_connection()
    if conn is None:
        return None, None

    cursor = conn.cursor()
    user_id = None

    try:
        conn.start_transaction()
        sql_campus = "INSERT INTO CampusUsers (RoleID, FullName, NIM_NIP, Email) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_campus, (role_id, full_name, nim_nip, email))
        campus_user_id = cursor.lastrowid

        sql_user = "INSERT INTO Users (CampusUserID, Username, PasswordHash, IsActive, IsAdmin) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_user, (campus_user_id, username, password_hash, False, False))
        user_id = cursor.lastrowid

        sql_token = "INSERT INTO EmailVerificationToken (UserID, Token, ExpiryTime) VALUES (%s, %s, %s)"
        cursor.execute(sql_token, (user_id, token, expiry_time))

        conn.commit()
        return user_id, token

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in create_new_user_with_token: {err}")
        return None, None
    finally:
        cursor.close()
        close_db_connection(conn)

def authenticate_user(username, plain_password):
    """Memverifikasi kredensial login pengguna."""
    conn = create_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    user_data = None

    try:
        sql_fetch_user = "SELECT UserID, PasswordHash, IsActive, IsAdmin FROM Users WHERE Username = %s"
        cursor.execute(sql_fetch_user, (username,))
        user = cursor.fetchone()

        if user:
            stored_password_hash = user['PasswordHash']
            is_active = user['IsActive']
            user_id = user['UserID']
            is_admin = user['IsAdmin']

            if check_password(plain_password, stored_password_hash):
                if is_active:
                    user_data = {'UserID': user_id, 'IsActive': is_active, 'IsAdmin': is_admin}
                else:
                    user_data = {'UserID': user_id, 'IsActive': is_active, 'IsAdmin': is_admin}

    except mysql.connector.Error as err:
        print(f"Database Error in authenticate_user: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return user_data

def activate_user_account(user_id):
    """Mengaktifkan akun pengguna."""
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
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in activate_user_account: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

def verify_email_token(user_id, token):
    """Memverifikasi token email dan mengaktifkan akun pengguna."""
    try:
        user_id = _convert_user_id(user_id)
        token = str(token)
    except (ValueError, TypeError) as e:
        print(f"Error converting parameters: {e}")
        return False

    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    verification_success = False
    
    try:
        conn.start_transaction()
        sql_find_token = """
            SELECT TokenID, ExpiryTime, IsUsed 
            FROM EmailVerificationToken 
            WHERE UserID = %s AND Token = %s
        """
        cursor.execute(sql_find_token, (user_id, token))
        token_data = cursor.fetchone()

        if token_data:
            token_id, expiry_time, is_used = token_data

            if is_used or expiry_time < datetime.datetime.now():
                conn.rollback()
                return False

            cursor.execute("UPDATE Users SET IsActive = TRUE WHERE UserID = %s", (user_id,))
            cursor.execute("UPDATE EmailVerificationToken SET IsUsed = TRUE WHERE TokenID = %s", (token_id,))
            conn.commit()
            verification_success = True

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in verify_email_token: {err}")
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error in verify_email_token: {e}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return verification_success

def request_password_reset(username_or_email):
    """Memproses permintaan reset password."""
    conn = create_db_connection()
    if conn is None:
        return None, None, None

    cursor = conn.cursor(dictionary=True)
    try:
        sql_find_user = """
            SELECT U.UserID, CU.Email
            FROM Users U
            JOIN CampusUsers CU ON U.CampusUserID = CU.CampusUserID
            WHERE U.Username = %s OR CU.Email = %s
        """
        cursor.execute(sql_find_user, (username_or_email, username_or_email))
        user = cursor.fetchone()

        if user:
            user_id = user['UserID']
            user_email = user['Email']
            reset_token = os.urandom(32).hex()
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=30)

            sql_insert_token = """
                INSERT INTO PasswordResetToken (UserID, Token, ExpiryTime, IsUsed)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_insert_token, (user_id, reset_token, expiry_time, False))
            conn.commit()
            return user_id, reset_token, user_email

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in request_password_reset: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
    return None, None, None

def reset_password_with_token(token, new_plain_password):
    """Memverifikasi token reset password dan mengupdate password."""
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    reset_success = False

    try:
        conn.start_transaction()
        sql_find_token = """
            SELECT TokenID, UserID, ExpiryTime, IsUsed 
            FROM PasswordResetToken 
            WHERE Token = %s
        """
        cursor.execute(sql_find_token, (token,))
        token_data = cursor.fetchone()

        if token_data:
            token_id, user_id, expiry_time, is_used = token_data

            if not is_used and expiry_time >= datetime.datetime.now():
                new_password_hash = hash_password(new_plain_password)
                cursor.execute("UPDATE Users SET PasswordHash = %s WHERE UserID = %s", (new_password_hash, user_id))
                cursor.execute("UPDATE PasswordResetToken SET IsUsed = TRUE WHERE TokenID = %s", (token_id,))
                conn.commit()
                reset_success = True

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database Error in reset_password_with_token: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return reset_success
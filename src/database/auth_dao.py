# src/database/auth_dao.py

import mysql.connector
import datetime
import random
import os
from src.database.db_connector import create_db_connection, close_db_connection
from src.utils.auth_utils import check_password, hash_password

def _convert_user_id(user_id):
    """Helper function to safely convert user_id to integer"""
    # Handle cases where user_id might be a single-element tuple from fetchone()
    if isinstance(user_id, (list, tuple)):
        if len(user_id) > 0:
            # Attempt to convert the first element to int
            try:
                return int(user_id[0])
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value inside tuple/list for user_id: {user_id[0]}")
        raise ValueError("Empty tuple or list received for user_id")
    # Handle cases where user_id is already an integer or string representation
    try:
        return int(user_id)
    except (ValueError, TypeError):
         raise ValueError(f"Cannot convert user_id to integer: {user_id}")


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
                 # Return user data regardless of active status,
                 # the GUI will handle the IsActive check
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
        # Ensure user_id is an integer and token is a string
        user_id = _convert_user_id(user_id) # Use the helper function
        token = str(token)
    except ValueError as e:
        print(f"Error converting parameters in verify_email_token: {e}")
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

            # Check if token is already used or expired
            if is_used or expiry_time < datetime.datetime.now():
                conn.rollback()
                return False

            # Activate user and mark token as used
            cursor.execute("UPDATE Users SET IsActive = TRUE WHERE UserID = %s", (user_id,))
            cursor.execute("UPDATE EmailVerificationToken SET IsUsed = TRUE WHERE TokenID = %s", (token_id,))
            conn.commit()
            verification_success = True
        else:
            # Token not found for the given user_id and token
            conn.rollback() # No changes were made, but good practice to rollback if transaction was started
            verification_success = False


    except mysql.connector.Error as err:
        if conn: # Ensure conn exists before rolling back
            conn.rollback()
        print(f"Database Error in verify_email_token: {err}")
        verification_success = False
    except Exception as e:
        if conn: # Ensure conn exists before rolling back
             conn.rollback()
        print(f"Unexpected error in verify_email_token: {e}")
        verification_success = False
    finally:
        if cursor:
            cursor.close()
        if conn:
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
            reset_token = os.urandom(32).hex() # Generate a secure random token
            expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=30) # Token valid for 30 minutes

            sql_insert_token = """
                INSERT INTO PasswordResetToken (UserID, Token, ExpiryTime, IsUsed)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_insert_token, (user_id, reset_token, expiry_time, False))
            conn.commit()
            return user_id, reset_token, user_email
        else:
             # User not found
             return None, None, None


    except mysql.connector.Error as err:
        if conn: # Ensure conn exists before rolling back
            conn.rollback()
        print(f"Database Error in request_password_reset: {err}")
        return None, None, None
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)

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

            # Check if token is not used and not expired
            if not is_used and expiry_time >= datetime.datetime.now():
                new_password_hash = hash_password(new_plain_password)
                cursor.execute("UPDATE Users SET PasswordHash = %s WHERE UserID = %s", (new_password_hash, user_id))
                cursor.execute("UPDATE PasswordResetToken SET IsUsed = TRUE WHERE TokenID = %s", (token_id,))
                conn.commit()
                reset_success = True
            else:
                 # Token invalid (used or expired)
                 conn.rollback() # No changes were made, but good practice
                 reset_success = False
        else:
            # Token not found
            conn.rollback() # No changes were made, but good practice
            reset_success = False


    except mysql.connector.Error as err:
        if conn: # Ensure conn exists before rolling back
            conn.rollback()
        print(f"Database Error in reset_password_with_token: {err}")
        reset_success = False
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)
        return reset_success

# --- New function to delete user and campus user ---
def delete_user_and_campus_user_by_id(user_id):
    """
    Deletes a user and their associated campus user record by UserID.
    Used for cleaning up accounts during canceled registration/verification.
    Returns True if successful, False otherwise.
    """
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        # Convert user_id to integer using the helper function
        user_id = _convert_user_id(user_id)

        conn.start_transaction() # Start transaction for atomicity

        # Get the CampusUserID before deleting the user
        sql_get_campus_id = "SELECT CampusUserID FROM Users WHERE UserID = %s"
        # Pass the integer user_id wrapped in a tuple
        cursor.execute(sql_get_campus_id, (user_id,))
        result = cursor.fetchone()

        if result:
            campus_user_id = result[0]

            # Delete from Users table
            sql_delete_user = "DELETE FROM Users WHERE UserID = %s"
            cursor.execute(sql_delete_user, (user_id,))

            # Delete from CampusUsers table
            sql_delete_campus = "DELETE FROM CampusUsers WHERE CampusUserID = %s"
            cursor.execute(sql_delete_campus, (campus_user_id,))

            # Optional: Delete related tokens (email verification, password reset)
            # This assumes foreign key ON DELETE CASCADE is NOT set up.
            # If CASCADE is set up, these deletes might be automatic.
            # sql_delete_email_tokens = "DELETE FROM EmailVerificationToken WHERE UserID = %s"
            # cursor.execute(sql_delete_email_tokens, (user_id,))
            # sql_delete_reset_tokens = "DELETE FROM PasswordResetToken WHERE UserID = %s"
            # cursor.execute(sql_delete_reset_tokens, (user_id,))

            conn.commit() # Commit the transaction
            success = True
        else:
            # User not found, consider it successful in terms of no record left
            print(f"Warning: User with ID {user_id} not found for deletion.")
            success = True # Or False if not finding is an error condition

    except ValueError as e:
        # Handle the case where _convert_user_id fails
        print(f"Error converting user_id in delete_user_and_campus_user_by_id: {e}")
        if conn: # Ensure conn exists before rolling back
            conn.rollback() # Rollback any potential implicit transaction
        success = False
    except mysql.connector.Error as err:
        if conn:
            conn.rollback() # Rollback on error
        print(f"Database error in delete_user_and_campus_user_by_id: {err}")
        success = False # Ensure success is False on error
    finally:
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn)
        return success

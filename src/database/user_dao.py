# src/database/user_dao.py

import mysql.connector
from src.database.db_connector import create_db_connection, close_db_connection

def get_all_users():
    """
    Retrieve all users (admin only)
    Returns list of user dictionaries or empty list if error
    """
    conn = create_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    users = []

    try:
        sql = """
            SELECT 
                u.UserID, 
                u.Username, 
                u.IsAdmin, 
                u.IsActive,
                cu.FullName,
                cu.NIM_NIP,
                cu.Email
            FROM Users u
            JOIN CampusUsers cu ON u.CampusUserID = cu.CampusUserID
            ORDER BY u.UserID
        """
        cursor.execute(sql)
        users = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database error in get_all_users: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return users

def update_admin_status(user_id, is_admin):
    """
    Update user admin status (admin only)
    Returns True if successful, False otherwise
    """
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        sql = "UPDATE Users SET IsAdmin = %s WHERE UserID = %s"
        cursor.execute(sql, (is_admin, user_id))
        conn.commit()
        success = True
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database error in update_admin_status: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

def delete_user(user_id):
    """
    Delete a user (admin only)
    Returns True if successful, False otherwise
    """
    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        # First get the CampusUserID to delete from both tables
        sql_get = "SELECT CampusUserID FROM Users WHERE UserID = %s"
        cursor.execute(sql_get, (user_id,))
        result = cursor.fetchone()

        if result:
            campus_user_id = result[0]

            # Transaction is implicitly started by the first execute() if autocommit is False.
            # conn.start_transaction() # <-- REMOVE THIS LINE

            # Delete from Users table
            sql_user = "DELETE FROM Users WHERE UserID = %s"
            cursor.execute(sql_user, (user_id,))

            # Delete from CampusUsers table
            sql_campus = "DELETE FROM CampusUsers WHERE CampusUserID = %s"
            cursor.execute(sql_campus, (campus_user_id,))

            conn.commit() # Commit the transaction encompassing both deletes
            success = True
        else:
             # User not found, consider it a success in terms of not failing the operation
             # but perhaps log a warning or return False depending on desired behavior
             print(f"Warning: User with ID {user_id} not found for deletion.")
             success = True # Or False if not finding is an error condition

    except mysql.connector.Error as err:
        # Rollback the transaction on any error
        if conn: # Ensure conn exists before rolling back
            conn.rollback()
        print(f"Database error in delete_user: {err}")
        success = False # Ensure success is False on error
    finally:
        # Always close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            close_db_connection(conn) # Assuming this function handles closing/pooling
        return success


def update_user_profile(user_id, full_name=None, nim_nip=None, email=None):
    """
    Update user profile information
    Returns True if successful, False otherwise
    """
    if not any([full_name, nim_nip, email]):
        return False  # Nothing to update

    conn = create_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    success = False

    try:
        # First get the CampusUserID
        sql_get = "SELECT CampusUserID FROM Users WHERE UserID = %s"
        cursor.execute(sql_get, (user_id,))
        result = cursor.fetchone()
        
        if result:
            campus_user_id = result[0]
            
            # Build dynamic update query
            updates = []
            params = []
            
            if full_name:
                updates.append("FullName = %s")
                params.append(full_name)
            if nim_nip:
                updates.append("NIM_NIP = %s")
                params.append(nim_nip)
            if email:
                updates.append("Email = %s")
                params.append(email)
            
            if updates:
                sql = f"UPDATE CampusUsers SET {', '.join(updates)} WHERE CampusUserID = %s"
                params.append(campus_user_id)
                cursor.execute(sql, params)
                conn.commit()
                success = True
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database error in update_user_profile: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return success

def get_user_profile(user_id):
    """
    Get complete user profile information
    Returns user dictionary or None if error/not found
    """
    conn = create_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    user = None

    try:
        sql = """
            SELECT 
                u.UserID,
                u.Username,
                u.IsAdmin,
                u.IsActive,
                cu.FullName,
                cu.NIM_NIP,
                cu.Email
            FROM Users u
            JOIN CampusUsers cu ON u.CampusUserID = cu.CampusUserID
            WHERE u.UserID = %s
        """
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database error in get_user_profile: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return user
    

def get_user_by_id(user_id):
    """
    Get a single user by ID (admin only)
    Returns user dictionary or None if not found/error
    """
    conn = create_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    user = None

    try:
        sql = """
            SELECT 
                u.UserID, 
                u.Username, 
                u.IsAdmin, 
                u.IsActive,
                cu.FullName,
                cu.NIM_NIP,
                cu.Email
            FROM Users u
            JOIN CampusUsers cu ON u.CampusUserID = cu.CampusUserID
            WHERE u.UserID = %s
        """
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database error in get_user_by_id: {err}")
    finally:
        cursor.close()
        close_db_connection(conn)
        return user

def toggle_admin_status(user_id):
    """
    Toggle user admin status (admin only)
    Returns new status if successful, None otherwise
    """
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    new_status = not user['IsAdmin']
    success = update_admin_status(user_id, new_status)
    
    return new_status if success else None
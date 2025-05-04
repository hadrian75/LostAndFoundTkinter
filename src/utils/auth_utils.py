# src/utils/auth_utils.py

import bcrypt # Menggunakan bcrypt untuk hashing password yang aman

def hash_password(password):
    """
    Menghasilkan hash bcrypt untuk password yang diberikan.
    Bcrypt secara otomatis menangani salt.
    """
    # Pastikan password adalah bytes sebelum hashing
    if isinstance(password, str):
        password = password.encode('utf-8')

    # Menghasilkan salt dan hash password
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode('utf-8') # Mengembalikan hash sebagai string utf-8

def check_password(password, hashed_password):
    """
    Memeriksa apakah password yang diberikan cocok dengan hash yang tersimpan.
    """
    # Pastikan password dan hashed_password adalah bytes sebelum perbandingan
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')

    # Membandingkan password dengan hash
    return bcrypt.checkpw(password, hashed_password)

# --- Test Block (Opsional) ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan auth_utils.py langsung
    print("Testing auth_utils functions...")

    # Password dummy untuk pengujian
    test_password = "mysecretpassword123"

    # Menguji hashing
    print(f"Hashing password: '{test_password}'")
    hashed = hash_password(test_password)
    print(f"Hashed password: {hashed}")

    # Menguji verifikasi (harus True)
    print(f"\nChecking password '{test_password}' against hash...")
    is_correct = check_password(test_password, hashed)
    print(f"Is password correct? {is_correct}")

    # Menguji verifikasi dengan password salah (harus False)
    wrong_password = "wrongpassword"
    print(f"\nChecking password '{wrong_password}' against hash...")
    is_correct_wrong = check_password(wrong_password, hashed)
    print(f"Is password correct? {is_correct_wrong}")

    # Menguji verifikasi dengan hash yang berbeda (harus False)
    another_hashed = hash_password("anotherpassword")
    print(f"\nChecking password '{test_password}' against a different hash...")
    is_correct_another_hash = check_password(test_password, another_hashed)
    print(f"Is password correct? {is_correct_another_hash}")

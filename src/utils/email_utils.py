# src/utils/email_utils.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Mengimpor konfigurasi SMTP dari src.config
from src.config import SMTP_CONFIG
import os # Import os untuk test block
from dotenv import load_dotenv # Import load_dotenv untuk test block

# --- Load environment variables for the test block ---
# Note: In the main application entry point (main.py),
# you should call load_dotenv() once at the very beginning.
# We include it here only for this specific test script to run standalone.
# If running the main app, this block can be commented out.
if __name__ == "__main__":
    load_dotenv()


def send_email(receiver_email, subject, body):
    """
    Mengirim email menggunakan konfigurasi SMTP eksternal dari config.py.

    Args:
        receiver_email (str): Alamat email penerima.
        subject (str): Subjek email.
        body (str): Isi email (plain text).

    Returns:
        bool: True jika email berhasil dikirim, False jika gagal.
    """
    # Ambil detail konfigurasi dari dictionary SMTP_CONFIG
    sender_email = SMTP_CONFIG.get('sender_email')
    sender_password = SMTP_CONFIG.get('sender_password') # Ini adalah App Password Google Anda
    smtp_host = SMTP_CONFIG.get('host')
    smtp_port = SMTP_CONFIG.get('port')

    # Lakukan validasi dasar pada konfigurasi
    # Pesan error ini akan muncul jika salah satu nilainya None atau kosong
    if not all([sender_email, sender_password, smtp_host, smtp_port]):
        print("Kesalahan konfigurasi SMTP: Detail pengirim atau server tidak lengkap di config.py atau .env.")
        return False

    try:
        # Membuat objek pesan email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Menambahkan isi email (plain text)
        msg.attach(MIMEText(body, 'plain'))

        # Menghubungkan ke SMTP server
        # Gunakan SMTP_SSL untuk port 465 (SSL)
        # Gunakan SMTP dan starttls() untuk port 587 (TLS)
        if smtp_port == 465:
            print(f"Connecting to SMTP server {smtp_host}:{smtp_port} using SSL...")
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        elif smtp_port == 587:
            print(f"Connecting to SMTP server {smtp_host}:{smtp_port} using TLS...")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls() # Mengamankan koneksi
        else:
             # Port lain, coba koneksi standar tanpa TLS/SSL (tidak disarankan untuk kredensial)
             print(f"Warning: Using standard SMTP connection on port {smtp_port} for {smtp_host}. TLS/SSL recommended.")
             server = smtplib.SMTP(smtp_host, smtp_port)


        # Login ke server SMTP
        print(f"Attempting to log in as {sender_email}...")
        server.login(sender_email, sender_password)
        print("Login successful.")

        # Mengirim email
        print(f"Attempting to send email to {receiver_email}...")
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully.")

        # Menutup koneksi
        server.quit()

        print(f"Email process completed from {sender_email} to {receiver_email} via {smtp_host}.")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Gagal mengirim email: Kesalahan autentikasi SMTP. Periksa SMTP_SENDER_EMAIL dan SMTP_SENDER_PASSWORD di .env. Pastikan App Password Google benar.")
        return False
    except smtplib.SMTPConnectError as e:
         print(f"Gagal mengirim email: Kesalahan koneksi SMTP. Pastikan SMTP_HOST dan SMTP_PORT benar, dan firewall tidak memblokir koneksi keluar. Error: {e}")
         return False
    except smtplib.SMTPException as e:
        print(f"Gagal mengirim email: Terjadi kesalahan SMTP: {e}")
        return False
    except Exception as e:
        print(f"Gagal mengirim email: Terjadi kesalahan tak terduga: {e}")
        return False

# --- Email Body Templates ---

def get_otp_email_body(user_full_name, otp_code, expiry_minutes=15):
    """
    Membuat isi email dengan template yang lebih santai untuk verifikasi OTP.

    Args:
        user_full_name (str): Nama lengkap pengguna.
        otp_code (str): Kode OTP yang dihasilkan.
        expiry_minutes (int): Durasi token berlaku dalam menit.

    Returns:
        str: Isi email dalam format teks biasa (dengan gaya santai).
    """
    # Mengambil nama depan jika nama lengkap memiliki spasi
    first_name = user_full_name.split(' ')[0] if ' ' in user_full_name else user_full_name

    body = f"""Halo {first_name}! 👋

Selamat datang di Campus Lost and Found System (CLFS)! 🎉

Untuk aktivasi akunmu, nih Kode Verifikasi Sekali Pakai (OTP) buat kamu:

✨ Kode OTP: {otp_code} ✨

Kode ini cuma berlaku {expiry_minutes} menit ya, jadi buruan dipake! Jangan kasih kode ini ke siapa-siapa, demi keamanan bareng. 😉

Kalau kamu nggak merasa daftar di CLFS, cuekin aja email ini ya.

Makasih udah gabung!

Salam,

Tim CLFS yang Keren 😎
"""
    return body

def get_reset_password_email_body(user_full_name, reset_token, expiry_minutes=30):
    """
    Membuat isi email untuk reset password.

    Args:
        user_full_name (str): Nama lengkap pengguna.
        reset_token (str): Token reset password yang dihasilkan.
        expiry_minutes (int): Durasi token berlaku dalam menit.

    Returns:
        str: Isi email dalam format teks biasa.
    """
    first_name = user_full_name.split(' ')[0] if ' ' in user_full_name else user_full_name

    # TODO: Ganti [Link ke halaman reset password dengan token ...] dengan URL asli
    # Di aplikasi Tkinter, Anda mungkin perlu instruksikan pengguna untuk membuka aplikasi
    # dan memasukkan token ini di halaman reset password.
    # Jika Anda punya web server, Anda bisa buat link seperti
    # f"http://your_app_url/reset-password?token={reset_token}"

    body = f"""Halo {first_name},

Kami menerima permintaan untuk mereset password akun CLFS Anda.

Kode token reset password Anda adalah:
{reset_token}

Kode ini berlaku selama {expiry_minutes} menit.

Mohon buka aplikasi CLFS dan masukkan kode token ini di halaman Reset Password.

Jika Anda tidak merasa melakukan permintaan ini, mohon abaikan email ini.

Hormat kami,

Tim CLFS
"""
    return body


# --- Test Block ---
if __name__ == "__main__":
    # Ini akan dijalankan hanya jika Anda menjalankan email_utils.py langsung
    print("Testing email_utils functions (using external SMTP)...")

    # Ganti dengan alamat email yang valid untuk pengujian
    # Ini akan mengirim email ke alamat ini
    test_receiver = "penerima_uji@example.com" # Ganti dengan email penerima yang sebenarnya
    
    # --- Test OTP Email ---
    # test_subject_otp = "Kode Aktivasi Akun CLFS Kamu nih! ✨"
    # test_user_name_otp = "Nama Pengguna Uji"
    # test_otp_code = "987654"
    # test_body_otp = get_otp_email_body(test_user_name_otp, test_otp_code, 10)
    # print(f"Attempting to send test OTP email to {test_receiver}...")
    # success_otp = send_email(test_receiver, test_subject_otp, test_body_otp)
    # if success_otp:
    #     print("Test OTP email sent successfully.")
    # else:
    #     print("Failed to send test OTP email.")

    # --- Test Reset Password Email ---
    test_subject_reset = "Instruksi Reset Password Akun CLFS Anda"
    test_user_name_reset = "Pengguna Reset Uji"
    test_reset_token = "a1b2c3d4e5f67890abcdef1234567890" # Token dummy
    test_body_reset = get_reset_password_email_body(test_user_name_reset, test_reset_token, 30)
    print(f"\nAttempting to send test Reset Password email to {test_receiver}...")
    success_reset = send_email(test_receiver, test_subject_reset, test_body_reset)
    if success_reset:
        print("Test Reset Password email sent successfully.")
    else:
        print("Failed to send test Reset Password email.")


    print("\nEmail utility testing finished.")


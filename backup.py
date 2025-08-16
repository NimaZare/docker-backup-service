import os
import zipfile
import datetime
import shutil
from ftplib import FTP
from dotenv import load_dotenv

# ===================== CONFIGURATION ===================== #
load_dotenv()

REMOTE_HOST = os.getenv("REMOTE_HOST")
REMOTE_USER = os.getenv("REMOTE_USER")
REMOTE_PASS = os.getenv("REMOTE_PASS")
REMOTE_DIR = os.getenv("REMOTE_DIR")

BACKUP_DIR = "/www/python_backup"
TODAY = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

SOURCES = {
    "AnonymousChatBot_data": "/www/python-applications/AnonymousChatBot/data",
    "IdeaBot_data": "/www/python-applications/IdeaBot/data",
    "DreamBot_db": "/www/python-applications/DreamBot/bot_data.db",
    "QABot_db": "/www/python-applications/QABot/qa_bot.db",
    "WriterBot_db": "/www/python-applications/WriterBot/bot_data.db",
}


# ===================== BACKUP FUNCTIONS ===================== #
def create_individual_backups():
    """Create zip backups for each source and keep only the 5 most recent."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for name, src in SOURCES.items():
        dest = os.path.join(BACKUP_DIR, name)
        os.makedirs(dest, exist_ok=True)
        zip_path = os.path.join(dest, f"{TODAY}.zip")

        if os.path.isdir(src):
            shutil.make_archive(zip_path[:-4], 'zip', src)
        elif os.path.isfile(src):
            with zipfile.ZipFile(zip_path, 'w', allowZip64=True) as zipf:
                zipf.write(src, os.path.basename(src))

        backups = sorted(os.listdir(dest), reverse=True)
        for backup in backups[5:]:
            os.remove(os.path.join(dest, backup))


def create_final_backup():
    """Create a combined zip file of today's backups."""
    final_zip = os.path.join(BACKUP_DIR, f"ALL_BACKUP_{TODAY}.zip")

    with zipfile.ZipFile(final_zip, 'w', allowZip64=True) as zipf:
        for name in SOURCES.keys():
            today_zip = os.path.join(BACKUP_DIR, name, f"{TODAY}.zip")
            if os.path.exists(today_zip):
                zipf.write(today_zip, os.path.join(name, f"{TODAY}.zip"))

    return final_zip


# ===================== FTP FUNCTIONS ===================== #
def check_ftp_connection():
    """Check if FTP connection works with provided credentials."""
    try:
        with FTP(REMOTE_HOST) as ftp:
            ftp.login(REMOTE_USER, REMOTE_PASS)
        return True
    except Exception as e:
        print(f"[ERROR] FTP connection failed: {e}")
        return False


def ensure_ftp_directory_exists(ftp, remote_dir):
    """Ensure that the remote directory exists on the FTP server, create if not."""
    try:
        ftp.cwd(remote_dir)
    except Exception:
        ftp.mkd(remote_dir)
        ftp.cwd(remote_dir)


def upload_to_ftp(local_file):
    """Upload final backup file to FTP and clean old files."""
    try:
        with FTP(REMOTE_HOST) as ftp:
            ftp.login(REMOTE_USER, REMOTE_PASS)
            ensure_ftp_directory_exists(ftp, REMOTE_DIR)

            with open(local_file, 'rb') as file:
                ftp.storbinary(f"STOR {os.path.basename(local_file)}", file)

            files = [f for f in ftp.nlst() if f not in ('.', '..')]
            files.sort(reverse=True)
            for old_file in files[5:]:
                try:
                    ftp.delete(old_file)
                except Exception as e:
                    print(f"[WARN] Could not delete {old_file}: {e}")

        print(f"\n[INFO] Backup uploaded successfully → {os.path.basename(local_file)} \n")
    except Exception as e:
        print(f"[ERROR] FTP upload failed: {e}")
        exit(1)


# ===================== MAIN EXECUTION ===================== #
def main():
    try:
        if not all([REMOTE_HOST, REMOTE_USER, REMOTE_PASS, REMOTE_DIR]):
            print("[ERROR] Missing FTP credentials in .env file! Exiting.")
            exit(1)

        if not check_ftp_connection():
            print(f"[ERROR] Cannot connect to FTP server {REMOTE_HOST}. Exiting.")
            exit(1)

        create_individual_backups()
        final_zip = create_final_backup()
        upload_to_ftp(final_zip)

        if os.path.exists(final_zip):
            os.remove(final_zip)
    
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()

# ===================== END ===================== #
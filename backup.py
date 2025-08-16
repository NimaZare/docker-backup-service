import os
import zipfile
import datetime
import shutil
from ftplib import FTP
from dotenv import load_dotenv

load_dotenv()

REMOTE_HOST = os.getenv("REMOTE_HOST")
REMOTE_USER = os.getenv("REMOTE_USER")
REMOTE_PASS = os.getenv("REMOTE_PASS")
REMOTE_DIR = os.getenv("REMOTE_DIR")

if not all([REMOTE_HOST, REMOTE_USER, REMOTE_PASS, REMOTE_DIR]):
    print("One or more FTP credentials are missing in .env! Exiting.")
    exit(1)

TODAY = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
BACKUP_DIR = "/www/python_backup"
SOURCES = {
    "AnonymousChatBot_data": "/www/python-applications/AnonymousChatBot/data",
    "IdeaBot_data": "/www/python-applications/IdeaBot/data",
    "DreamBot_db": "/www/python-applications/DreamBot/bot_data.db",
    "QABot_db": "/www/python-applications/QABot/qa_bot.db",
    "WriterBot_db": "/www/python-applications/WriterBot/bot_data.db",
}

os.makedirs(BACKUP_DIR, exist_ok=True)

for name, src in SOURCES.items():
    dest = os.path.join(BACKUP_DIR, name)
    os.makedirs(dest, exist_ok=True)
    zip_path = os.path.join(dest, f"{TODAY}.zip")

    if os.path.isdir(src):
        shutil.make_archive(zip_path[:-4], 'zip', src)
    elif os.path.isfile(src):
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(src, os.path.basename(src))

    backups = sorted(os.listdir(dest), reverse=True)
    for backup in backups[5:]:
        os.remove(os.path.join(dest, backup))

FINAL_ZIP = os.path.join(BACKUP_DIR, f"ALL_BACKUP_{TODAY}.zip")
with zipfile.ZipFile(FINAL_ZIP, 'w', allowZip64=True) as zipf:
    for name in SOURCES.keys():
        today_zip = os.path.join(BACKUP_DIR, name, f"{TODAY}.zip")
        if os.path.exists(today_zip):
            zipf.write(today_zip, os.path.join(name, f"{TODAY}.zip"))


def check_ftp_connection(host):
    try:
        with FTP(host) as ftp:
            ftp.login(REMOTE_USER, REMOTE_PASS)
            return True
    except Exception as e:
        print(f"FTP connection failed: {e}")
        return False

if not check_ftp_connection(REMOTE_HOST):
    print(f"Cannot connect to FTP server {REMOTE_HOST}. Exiting.")
    exit(1)

def ensure_ftp_directory_exists(ftp, remote_dir):
    """Ensure that the remote directory exists on the FTP server, create if not."""
    try:
        ftp.cwd(remote_dir)
    except Exception:
        ftp.mkd(remote_dir)
        ftp.cwd(remote_dir)

def upload_to_ftp(local_file, remote_path):
    try:
        with FTP(REMOTE_HOST) as ftp:
            ftp.login(REMOTE_USER, REMOTE_PASS)
            ensure_ftp_directory_exists(ftp, remote_path)
            
            with open(local_file, 'rb') as file:
                ftp.storbinary(f"STOR {os.path.basename(local_file)}", file)
            
            files = [f for f in ftp.nlst() if f not in ('.', '..')]
            files.sort(reverse=True)
            for old_file in files[5:]:
                try:
                    ftp.delete(old_file)
                except Exception as e:
                    print(f"Could not delete {old_file}: {e}")
        
        print(f"--------------------\n({TODAY}) backup completed successfully\n")
    except Exception as e:
        print(f"FTP upload failed: {e}")
        exit(1)

upload_to_ftp(FINAL_ZIP, REMOTE_DIR)

if os.path.exists(FINAL_ZIP):
    os.remove(FINAL_ZIP)

#+++++++++++++++++++++++++++ END ++++++++++++++++++++++++++
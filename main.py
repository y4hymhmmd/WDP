import subprocess
import time
from keep_alive import keep_alive

def install_requirements():
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

# Menginstal dependencies dari requirements.txt
install_requirements()

# Memulai server Flask (atau fungsi serupa)
keep_alive()

# Menjalankan script pertama
subprocess.Popen(["python3", "insta.py"])

# Tunggu beberapa detik untuk memastikan script pertama memulai
time.sleep(10)

# Menjalankan script kedua
subprocess.Popen(["python3", "script.py"])

# Menjaga agar main.py tetap berjalan
while True:
    time.sleep(60)

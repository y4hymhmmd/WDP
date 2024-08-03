import os
import time
import signal
import sys
import json
import requests
from datetime import datetime
from instagrapi import Client
from rich.console import Console

# Inisialisasi console Rich
console = Console()

# Daftar akun Instagram
accounts = [{
    'username': 'wdp1k_bot3',
    'password': 'WDP1K09876'
}, {
    'username': 'wdp1k_bot2',
    'password': 'WDP1K09876'
}]

# Inisialisasi klien instagrapi
cl = Client()

# Telegram bot token dan chat ID
telegram_token = '7118973544:AAEfZm8GWoKHa-NDWyIhKCwX5dXbf4s07vg'
chat_id = '6105931152'

# Fungsi untuk mengirim pesan ke Telegram
def send_telegram_message(token, chat_id, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=payload)
    if not response.ok:
        console.print(f"[bold red]Failed to send message: {response.text}[/bold red]")

def save_session(username):
    session_data = cl.get_settings()
    with open(f'{username}_session.json', 'w') as f:
        json.dump(session_data, f)
    console.print("[bold green]Session saved successfully![/bold green]")

def load_session(username):
    if os.path.exists(f'{username}_session.json'):
        with open(f'{username}_session.json', 'r') as f:
            session_data = json.load(f)
        cl.set_settings(session_data)
        console.print("[bold green]Session loaded successfully![/bold green]")
        return True
    return False

def login():
    for account in accounts:
        username = account['username']
        password = account['password']
        if load_session(username):
            return

        try:
            cl.login(username, password)
            save_session(username)
            console.print(
                f"[bold green]Login successful for {username}![/bold green]")
            return
        except Exception as e:
            console.print(
                f"[bold red]Login error for {username}:[/bold red] {e}")
            send_telegram_message(telegram_token, chat_id, f"Login error for {username}: {e}")
            if "challenge_required" in str(e).lower():
                console.print(
                    "[bold red]Challenge required. Switching accounts...[/bold red]"
                )
                continue  # Try the next account
            else:
                sys.exit(1)

    console.print(
        "[bold red]All accounts failed to login due to challenge required.[/bold red]"
    )
    sys.exit(1)

login()

# Nama akun Instagram yang ingin Anda unduh postingannya
profile_name = 'cl0udymoody_'

# Direktori tempat menyimpan unduhan
download_directory = profile_name
downloaded_posts_file = f"{profile_name}_downloaded_posts.txt"

def load_downloaded_posts():
    if os.path.exists(downloaded_posts_file):
        with open(downloaded_posts_file, 'r') as file:
            return set(file.read().splitlines())
    return set()

def save_downloaded_post(post_id):
    with open(downloaded_posts_file, 'a') as file:
        file.write(f"{post_id}\n")

def download_new_posts():
    # Membuat direktori jika belum ada
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    downloaded_posts = load_downloaded_posts()
    new_post_downloaded = False

    try:
        user_id = cl.user_id_from_username(profile_name)
        console.print(
            f"[bold cyan]User ID for {profile_name}: {user_id}[/bold cyan]")
        all_posts = cl.user_medias(user_id, 0)  # Ambil semua postingan
        console.print(
            f"[bold cyan]Total posts fetched: {len(all_posts)}[/bold cyan]")

        for post in all_posts:
            post_id = post.pk
            post_date = post.taken_at.date().strftime("%Y-%m-%d")
            filename = f"{profile_name}_{post_date}_{post_id}"
            media_path = os.path.join(download_directory, filename)

            if post_id not in downloaded_posts:
                try:
                    cl.photo_download_by_url(post.thumbnail_url, media_path)
                    save_downloaded_post(post_id)
                    new_post_downloaded = True
                    console.print(
                        f"[bold green]Downloaded new post to:[/bold green] {media_path}"
                    )
                except Exception as download_error:
                    console.print(
                        f"[bold yellow]Failed to download {post_id}: {download_error}[/bold yellow]"
                    )
                    send_telegram_message(telegram_token, chat_id, f"Failed to download {post_id}: {download_error}")
            else:
                console.print(
                    f"[bold cyan]Post {post_id} already downloaded. Skipping...[/bold cyan]"
                )

    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")
        send_telegram_message(telegram_token, chat_id, f"An error occurred: {e}")
        if "login_required" in str(e).lower():
            handle_login_required_error()
    return new_post_downloaded

def handle_login_required_error():
    console.print(
        "[bold red]Login required error encountered. Restarting script with next account...[/bold red]"
    )
    send_telegram_message(telegram_token, chat_id, "Login required error encountered. Restarting script with next account...")
    sys.exit(1)

def signal_handler(sig, frame):
    console.print('\n[bold red]Skrip dihentikan secara manual![/bold red]')
    send_telegram_message(telegram_token, chat_id, "Script stopped manually.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

check_interval = 1  # Tunggu detik sebelum cek berikutnya

# Menyimpan postingan yang sudah diunduh untuk dicetak hanya sekali
printed_posts = set()

while True:
    start_time = time.time()
    new_post_downloaded = download_new_posts()
    end_time = time.time()
    elapsed_time = end_time - start_time

    if not new_post_downloaded:
        console.print(
            f"[bold cyan]No new posts to download. Waiting for {check_interval} seconds before the next check...[/bold cyan]"
        )
    else:
        console.print(
            f"[bold cyan]Waiting for {check_interval} seconds before checking again...[/bold cyan]"
        )

    time_to_wait = check_interval - elapsed_time
    if time_to_wait > 0:
        time.sleep(time_to_wait)

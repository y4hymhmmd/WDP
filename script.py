import os
import time
import numpy as np
import requests
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image, UnidentifiedImageError

# Fungsi untuk ekstraksi fitur dari gambar
def extract_features(img_path, model):
    try:
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        features = model.predict(img_array)
        return features
    except UnidentifiedImageError as e:
        print(f"Error: {e} - Skipping file {img_path}")
        return None

# Fungsi untuk mengirim pesan dan gambar ke Telegram
def send_telegram_message_with_photo(token, chat_id, photo_path, caption):
    url = f'https://api.telegram.org/bot{token}/sendPhoto'
    with open(photo_path, 'rb') as photo:
        payload = {
            'chat_id': chat_id,
            'caption': caption,
            'parse_mode': 'Markdown'  # Menggunakan Markdown untuk format pesan
        }
        files = {'photo': photo}
        response = requests.post(url, data=payload, files=files)
        if not response.ok:
            print(f"Failed to send message: {response.text}")

# Fungsi untuk mengirim pesan teks ke Telegram
def send_telegram_message(token, chat_id, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'  # Menggunakan Markdown untuk format pesan
    }
    response = requests.post(url, data=payload)
    if not response.ok:
        print(f"Failed to send message: {response.text}")

# Fungsi untuk menemukan gambar yang mirip
def find_similar_images(query_image_path, folder_path, model, similarity_threshold=0.8, processed_images=set(), telegram_token=None, chat_id=None):
    try:
        image_list = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        image_list = [img for img in image_list if img not in processed_images]

        if not image_list:
            print("Tidak ada gambar baru untuk diperiksa.")
            return []

        print(f"Processing {len(image_list)} images...")
        query_features = extract_features(query_image_path, model)
        if query_features is None:
            return []

        similarities = []

        for img_path in image_list:
            img_features = extract_features(img_path, model)
            if img_features is not None:
                similarity = cosine_similarity(query_features, img_features)[0][0]
                similarities.append((img_path, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)

        similar_images = [(img_path, similarity) for img_path, similarity in similarities if similarity >= similarity_threshold]

        if similar_images:
            for img_path, similarity in similar_images:
                message = (
                    f"*Gambar yang mirip dengan {query_image_path} ditemukan:*\n\n"
                    f"📸 *Gambar:* {img_path}\n"
                    f"🔍 *Similarity:* `{similarity:.4f}`"
                )

                if telegram_token and chat_id:
                    send_telegram_message_with_photo(telegram_token, chat_id, img_path, message)

                print(message)
        else:
            print("Tidak ada gambar yang mirip ditemukan.")

        processed_images.update(image_list)
        return similar_images
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        if telegram_token and chat_id:
            send_telegram_message(telegram_token, chat_id, error_message)
        return []

# Inisialisasi model MobileNetV2
model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

folder_path = 'xcashshop_'  # Ganti dengan path folder Anda
query_image_path = 'xcashshop_/xcashshop__2024-07-31_3424101646553449774.jpg'

similarity_threshold = 0.78  # Ubah sesuai kebutuhan Anda

telegram_token = '7118973544:AAEfZm8GWoKHa-NDWyIhKCwX5dXbf4s07vg'
chat_id = '6105931152'

processed_images = set()

try:
    while True:
        find_similar_images(query_image_path, folder_path, model, similarity_threshold, processed_images, telegram_token, chat_id)
        time.sleep(1)  # Tunggu 1 detik sebelum memeriksa gambar baru
except KeyboardInterrupt:
    print("Program dihentikan oleh pengguna.")
    send_telegram_message(telegram_token, chat_id, "Program dihentikan oleh pengguna.")

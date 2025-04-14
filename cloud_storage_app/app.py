import os
import hashlib
import streamlit as st
from PIL import Image
import io

import firebase_admin
from firebase_admin import credentials, storage

from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import requests

# MongoDB Initialization
MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
mongo_db = client["cloud_storage_db"]
hashes_collection = mongo_db["image_hashes"]

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'cloud-2f36e.firebasestorage.app'
    })
bucket = storage.bucket()

# Local storage (for fallback or previewing)
STORAGE_FOLDER = "cloud_storage"
os.makedirs(STORAGE_FOLDER, exist_ok=True)

# ==== Storage Virtualization Classes ====

class StorageBackend:
    def exists(self, filename): pass
    def save(self, filename, data): pass
    def get_url(self, filename): pass
    def get_image_data(self, filename): pass

class CloudinaryStorage(StorageBackend):
    def __init__(self):
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"]
        )

    def exists(self, filename):
        return False

    def save(self, filename, data):
        try:
            result = cloudinary.uploader.upload(io.BytesIO(data), public_id=f"uploads/{filename}", resource_type="image")
            return result['secure_url']
        except Exception as e:
            st.error(f"Cloudinary upload error: {str(e)}")
            raise

    def get_url(self, filename):
        return f"https://res.cloudinary.com/{st.secrets['cloudinary']['cloud_name']}/image/upload/uploads/{filename}"

    def get_image_data(self, filename):
        try:
            url = self.get_url(filename)
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            else:
                return None
        except Exception as e:
            st.error(f"Cloudinary fetch error: {str(e)}")
            return None

class FirebaseStorage(StorageBackend):
    def exists(self, filename):
        try:
            return bucket.blob(f"uploads/{filename}").exists()
        except Exception as e:
            st.error(f"Firebase error: {str(e)}")
            return False

    def save(self, filename, data):
        try:
            blob = bucket.blob(f"uploads/{filename}")
            blob.upload_from_string(data, content_type="image/jpeg")
            blob.make_public()
            return blob.public_url
        except Exception as e:
            st.error(f"Firebase upload error: {str(e)}")
            raise

    def get_url(self, filename):
        try:
            return bucket.blob(f"uploads/{filename}").public_url
        except Exception as e:
            st.error(f"Firebase URL error: {str(e)}")
            return None

    def get_image_data(self, filename):
        try:
            blob = bucket.blob(f"uploads/{filename}")
            return blob.download_as_bytes()
        except Exception as e:
            st.error(f"Firebase download error: {str(e)}")
            return None

class LocalStorage(StorageBackend):
    def __init__(self, folder):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def exists(self, filename):
        return os.path.exists(os.path.join(self.folder, filename))

    def save(self, filename, data):
        try:
            with open(os.path.join(self.folder, filename), "wb") as f:
                f.write(data)
        except Exception as e:
            st.error(f"Local save error: {str(e)}")
            raise

    def get_url(self, filename):
        return os.path.join(self.folder, filename)

    def get_image_data(self, filename):
        try:
            with open(os.path.join(self.folder, filename), "rb") as f:
                return f.read()
        except Exception as e:
            st.error(f"Local read error: {str(e)}")
            return None

# ==== Helper Functions ====

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    if not username.isalnum():
        return False

    users_collection = mongo_db["users"]
    user = users_collection.find_one({"username": username})
    hashed_pw = hash_password(password)

    if user:
        return hashed_pw == user["password_hash"]
    else:
        users_collection.insert_one({
            "username": username,
            "password_hash": hashed_pw,
            "uploads": []
        })
        return True

def calculate_hash(image_data):
    return hashlib.md5(image_data).hexdigest()

def cleanup_invalid_images(username):
    user = mongo_db["users"].find_one({"username": username})
    if not user or "uploads" not in user:
        return

    valid_uploads = []
    for img in user["uploads"]:
        try:
            response = requests.get(img["url"])
            if response.status_code == 200:
                valid_uploads.append(img)
            else:
                hashes_collection.delete_one({"hash": img["hash"]})
        except:
            continue

    mongo_db["users"].update_one(
        {"username": username},
        {"$set": {"uploads": valid_uploads}}
    )

def compress_and_reformat(image_data, quality=85):
    try:
        img = Image.open(io.BytesIO(image_data))
        if img.size[0] * img.size[1] > 10_000_000:
            raise ValueError("Image too large")
        img = img.convert("RGB")
        output_buffer = io.BytesIO()
        img.save(output_buffer, "JPEG", quality=quality)
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"Image processing error: {str(e)}")
        return None

def choose_storage_backend(compressed_data):
    if len(compressed_data) <= 140 * 1024:
        return FirebaseStorage()
    else:
        return CloudinaryStorage()

def upload_image(username, image_data, file_name):
    img_hash = calculate_hash(image_data)
    file_ext = os.path.splitext(file_name)[1].lower()
    final_name = f"{img_hash}__compressed.jpg"

    if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return "Invalid file format. Please upload an image."

    existing = hashes_collection.find_one({"hash": img_hash})
    if existing:
        url = existing["url"]
        mongo_db["users"].update_one(
            {"username": username},
            {"$addToSet": {"uploads": {
                "filename": final_name,
                "url": url,
                "hash": img_hash
            }}}
        )
        return f"🟡 Duplicate image detected. [View Image]({url})"

    compressed_data = compress_and_reformat(image_data)
    if compressed_data is None:
        return "Image processing failed"

    storage_backend = choose_storage_backend(compressed_data)
    try:
        url = storage_backend.save(final_name, compressed_data)

        hashes_collection.insert_one({
            "hash": img_hash,
            "filename": final_name,
            "url": url,
            "uploaded_by": username
        })

        mongo_db["users"].update_one(
            {"username": username},
            {"$addToSet": {"uploads": {
                "filename": final_name,
                "url": url,
                "hash": img_hash
            }}}
        )

        return f"✅ Image uploaded successfully!\n🔗 [View]({url})"
    except Exception as e:
        return f"❌ Upload failed: {str(e)}"

def get_user_images(username):
    user = mongo_db["users"].find_one({"username": username})
    if user and "uploads" in user:
        return [(img["filename"], img["url"]) for img in user["uploads"]]
    return []

# ==== Main App ====

def main():
    st.set_page_config(page_title="Cloud Storage App", page_icon="☁️", layout="wide")
    st.title("☁️ Cloud Storage with Firebase & Cloudinary")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    with st.sidebar:
        st.header("Login / Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login / Register")

        if login_button:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                authenticated = authenticate_user(username, password)
                if authenticated:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success(f"Welcome, {username}!")

                    # 🔄 Cleanup invalid image links on login
                    cleanup_invalid_images(username)
                else:
                    st.error("Authentication failed")

        if st.session_state.get("authenticated", False):
            st.write(f"Logged in as: {st.session_state.username}")
            logout_button = st.button("Logout")

            if logout_button:
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    if st.session_state.get("authenticated", False):
        tab1, tab2 = st.tabs(["📤 Upload Images", "📁 View Images"])

        with tab1:
            st.header("Upload New Image")
            uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'jpeg', 'png', 'gif', 'bmp'])
            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Preview", width=300)
                    if st.button("Upload Image"):
                        uploaded_file.seek(0)
                        result = upload_image(
                            st.session_state.username,
                            uploaded_file.getvalue(),
                            uploaded_file.name
                        )
                        st.success(result)
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

        with tab2:
            st.header("Your Uploaded Images")

            if st.button("🔄 Cleanup Broken Links"):
                cleanup_invalid_images(st.session_state.username)
                st.success("Cleaned up broken image links.")
                st.rerun()

            images = get_user_images(st.session_state.username)
            if not images:
                st.info("You haven't uploaded any images yet.")
            else:
                cols = st.columns(3)
                for idx, (img_name, public_url) in enumerate(images):
                    with cols[idx % 3]:
                        try:
                            if public_url.startswith('http'):
                                st.image(public_url, caption=img_name, use_container_width=True)
                            else:
                                storage_backend = LocalStorage(STORAGE_FOLDER)
                                img_data = storage_backend.get_image_data(img_name)
                                if img_data:
                                    st.image(img_data, caption=img_name, use_container_width=True)
                                else:
                                    st.error(f"Could not load image: {img_name}")
                            st.markdown(f"[Open]({public_url})", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error displaying image: {str(e)}")

    else:
        st.info("Please login or register to use the app.")

if __name__ == "__main__":
    main()
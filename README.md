# ☁️ Cloud Storage App (Streamlit + Firebase + Cloudinary)

A **Streamlit web app** that allows users to securely upload, store, and view images in the cloud.  
It uses **MongoDB** for authentication and metadata, **Firebase Storage** for smaller images, and **Cloudinary** for larger images.  
The app also includes deduplication (via hashing) and automatic cleanup of broken image links.

---

## ✨ Features
✅ **User Authentication** (login/register with MongoDB)  
✅ **Image Uploading** with compression and format conversion  
✅ **Dual Cloud Backends**:
  - Small images (≤140 KB) → **Firebase Storage**
  - Large images → **Cloudinary**
✅ **Deduplication**: Detects duplicate images by hash and avoids re‑uploads  
✅ **Broken Link Cleanup**: Removes stale image references on login or on demand  
✅ **Responsive Gallery**: View uploaded images with public links

---

## 🖥️ Tech Stack
| Component | Technology |
|-----------|------------|
| Frontend | [Streamlit](https://streamlit.io/) |
| Database | MongoDB Atlas |
| Cloud Storage | Firebase Storage & Cloudinary |
| Image Processing | Pillow (PIL) |
| Language | Python 3.9+ |

---

## 📂 Project Structure
cloud-storage-app/
├── app.py                 # Main Streamlit app
├── requirements.txt       # Python dependencies
├── .streamlit/secrets.toml # Store API keys & credentials securely
└── README.md

---

## 🚀 Getting Started

### 1️⃣ Prerequisites
- Python 3.9+ installed
- MongoDB Atlas cluster URI
- Firebase project with storage bucket
- Cloudinary account (API key & secret)
- Streamlit installed

---


requirements.txt should include:
streamlit
pillow
firebase-admin
pymongo
cloudinary
requests
certifi

### 2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Configure Secrets

In .streamlit/secrets.toml, add:

[mongo_uri]
mongo_uri = "YOUR_MONGO_ATLAS_CONNECTION_STRING"

[firebase_credentials]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"

[firebase]
storage_bucket = "your-firebase-project.appspot.com"

[cloudinary]
cloud_name = "your-cloud-name"
api_key = "your-api-key"
api_secret = "your-api-secret"

4️⃣ Run the App
streamlit run app.py


The app will open in your browser at:
http://localhost:8501


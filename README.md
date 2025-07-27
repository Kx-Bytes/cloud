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

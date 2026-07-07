# 🏕️ PTA Scout Adventure 2026
**Platform Manajemen Lomba Pramuka – Full-Stack Flask + Real-time Quiz**

---

## 🚀 Cara Menjalankan (Lokal)

```bash
# 1. Clone & masuk folder
cd pta_scout

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Konfigurasi .env
cp .env.example .env
# Edit .env sesuai kebutuhan

# 5. Jalankan aplikasi
python app.py
```
Buka: **http://localhost:5000**
Login Admin default: `admin` / `admin123`

---

## 📁 Struktur Folder

```
pta_scout/
├── app.py                  # App factory, SocketIO init, seed data
├── models.py               # SQLAlchemy models
├── requirements.txt
├── Procfile                # Untuk Heroku/Railway/Render
├── .env.example
├── routes/
│   ├── auth.py             # Login/logout
│   ├── admin.py            # Semua CRUD admin
│   ├── participant.py      # Dashboard peserta
│   ├── quiz.py             # Quiz engine + scoring
│   ├── api.py              # JSON API endpoints
│   └── socket_events.py    # Real-time Socket.IO
└── templates/
    ├── base.html           # Layout utama
    ├── login.html          # Halaman login
    ├── admin.html          # Dashboard admin
    ├── dashboard.html      # Dashboard peserta
    ├── quiz.html           # Real-time quiz
    └── leaderboard.html    # Live leaderboard
```

---

## ⚙️ Fitur Lengkap

### 👤 Admin
- ✅ Tambah/hapus Sangga dan anggota
- ✅ Kontrol XP manual (bonus/punishment) dengan log audit
- ✅ Buat/hapus misi dengan link referensi
- ✅ Gatekeeper: kunci/buka akses misi per hari
- ✅ Buat kuis pilihan ganda
- ✅ Aktifkan/nonaktifkan kuis secara live
- ✅ Review & approve submission misi

### 🎯 Peserta
- ✅ Dashboard dengan progress bar & leaderboard
- ✅ Submit bukti misi via link
- ✅ Ikut kuis real-time (speed-based scoring)
- ✅ Profil kontribusi XP individu ke Sangga

### 🧠 Quiz Engine
- **Speed-based XP**: Makin cepat jawab = makin banyak XP
- **Formula**: `XP = base_xp × (0.2 + 0.8 × speed_ratio)`
- **Min XP**: 20% dari base_xp jika benar tapi lambat
- **Auto akumulasi**: XP individu → total XP Sangga
- **Real-time broadcast**: via Socket.IO

---

## 🌐 Deploy ke Production

### Railway / Render
1. Push ke GitHub
2. Connect ke Railway/Render
3. Set environment variable `SECRET_KEY` dan `DATABASE_URL`
4. Deploy!

### Heroku
```bash
heroku create nama-app
heroku config:set SECRET_KEY=rahasia-panjang
git push heroku main
```

### VPS (Ubuntu)
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
# Gunakan Nginx sebagai reverse proxy
```

---

## 🔒 Keamanan Production
- Ganti `SECRET_KEY` di `.env` (minimal 32 karakter acak)
- Gunakan PostgreSQL untuk production
- Aktifkan HTTPS di hosting
- Set `SESSION_COOKIE_SECURE=True` jika HTTPS

---

## 📱 Mobile-Friendly
Semua halaman dioptimalkan untuk HP dengan:
- Tailwind responsive classes
- Font ringan (Cinzel + Lato via Google Fonts)
- Minimal JavaScript payload
- Touch-friendly button sizes

---

*Dibuat dengan ❤️ untuk Pramuka Indonesia* 🇮🇩

# IS 1 Assistant Bot 🤖

Discord bot asisten untuk mahasiswa Sistem Informasi IS 1 dengan AI chatbot (Groq), manajemen jadwal kuliah, dan reminder pribadi.

## ✨ Fitur Utama

### 🤖 AI Chatbot
- Powered by Groq (llama-3.1-8b-instant)
- Persona khusus untuk mahasiswa IS 1
- Auto-inject database context (tidak mengarang data)
- Rate limiting (3 detik cooldown) untuk prevent spam
- Rich presence: "Listening to IS ONLY ONE"

### 📅 Manajemen Jadwal
- Tambah jadwal kuliah via text command
- Lihat jadwal per hari, per mata kuliah, atau semua
- Hapus jadwal berdasarkan mata kuliah
- Auto-announcement jadwal harian
- Slash commands untuk admin (tambah/hapus/clear)

### ⏰ Reminder Pribadi
- Buat reminder dengan format fleksibel (1h30m, 2d, 45m)
- Notifikasi via DM saat reminder tiba
- Lihat daftar reminder aktif
- Hapus semua reminder sekaligus

### 🔐 Security & Privacy
- **Sensitive data filter** - Bot menolak menyimpan data sensitif seperti:
  - Password, PIN, OTP
  - KTP, NIK, NPWP
  - Kartu kredit, CVV, rekening
  - API keys, tokens, private keys
- Channel restriction untuk AI chat
- Admin-only commands

### 📊 Analytics
- Usage tracking di `analytics.log`
- Log command execution per user

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Environment
Buat file `.env`:
```env
# Discord Bot
BOT_TOKEN=your_discord_bot_token

# Groq AI
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant  # optional
GROQ_TEMPERATURE=0.3             # optional
GROQ_MAX_TOKENS=400              # optional
```

### 3. Setup Channel ID
Edit `bot.py` untuk set channel yang diizinkan:
```python
GROQ_ALLOWED_CHANNELS = [1234567890]  # Channel ID Discord
```

### 4. Jalankan Bot
```bash
python bot.py
```

## 📝 Command List

### 🗣️ Natural Language Commands (AI-Powered)
Bot sekarang mengerti perintah dalam bahasa natural! Tidak perlu format yang ketat lagi.

#### Reminder (Natural Language)
```
"ingatkan aku dalam 5 menit untuk belajar"
"reminder dalam 2 jam untuk makan"
"ingat aku dalam 30 detik untuk submit tugas"
"dalam 1 hari ingetin aku untuk tidur"
```

**Delete Reminder:**
```
"hapus reminder belajar"        # Delete reminder with keyword "belajar"
"hapus reminder terbaru"        # Delete latest reminder
"hapus semua reminder"          # Delete all reminders
```

#### Jadwal (Natural Language)
**Add Schedule:**
```
"tambahkan jadwal senin jam 08:00 kuliah AI"
"tambah jadwal rabu 14:30 pemrograman web"
"jadwal jumat pukul 10:00 basis data"
```

**Delete Schedule:**
```
"hapus jadwal senin jam 08:00"
"delete schedule rabu 14:30"
```

---

### Text Commands (Traditional Format)
| Command | Deskripsi | Contoh |
|---------|-----------|--------|
| `tambah jadwal [Hari] [HH:MM] [Matkul]` | Tambah jadwal | `tambah jadwal Senin 09:00 Matdis` |
| `jadwal` | Lihat jadwal hari ini | `jadwal` |
| `jadwal [Hari]` | Lihat jadwal hari tertentu | `jadwal Selasa` |
| `jadwal [Matkul]` | Cari jadwal mata kuliah | `jadwal Basis Data` |
| `jadwal semua` | Lihat semua jadwal | `jadwal semua` |
| `hapus jadwal [Matkul]` | Hapus jadwal by matkul | `hapus jadwal Matdis` |
| `tambah reminder [durasi] [pesan]` | Buat reminder | `tambah reminder 1h30m belajar` |
| `lihat reminder` | Lihat reminder aktif | `lihat reminder` |
| `hapus reminder` | Hapus semua reminder | `hapus reminder` |
| `help` / `bantuan` | Lihat daftar command | `help` |

### Slash Commands (untuk semua)
- `/isschedule [hari]` - Lihat jadwal kuliah
- `/isremind` - Pasang reminder (via form)
- `/ishelp` - Daftar perintah lengkap
- `/ping` - Cek latensi bot

### Admin Commands
- `/isinfo [pesan]` - Kirim pengumuman dengan tag role
- `/isaddschedule` - Tambah jadwal (via form)
- `/isremovetime [hari] [jam]` - Hapus jadwal jam tertentu
- `/isclearschedule [hari]` - Hapus semua jadwal di hari tertentu
- `/isannounce` - Kirim pesan ke channel lain (via form)

## 💬 Cara Menggunakan AI Chat

1. **Mention bot** di channel yang diizinkan:
   ```
   @IS 1 Assistant Apa itu algoritma?
   ```

2. **Reply pesan bot** untuk melanjutkan percakapan:
   ```
   [reply ke bot] Jelaskan lebih detail dong
   ```

3. **Tanya tentang jadwal/reminder:**
   ```
   @IS 1 Assistant Ada jadwal apa hari ini?
   ```

## 🛡️ Security Features

### Sensitive Data Filter
Bot akan **menolak** menyimpan data yang mengandung kata kunci sensitif:
- ❌ `tambah jadwal Senin 09:00 Password123`
- ❌ `tambah reminder 1h KTP 123456`
- ✅ `tambah jadwal Senin 09:00 Matematika Diskrit`

### Rate Limiting
- Cooldown 3 detik per user untuk AI chat
- Prevent spam dan abuse

### Database
- `schedule.db` - Menyimpan jadwal dan reminder
- Otomatis dibuat saat pertama kali run
- **Jangan commit database ke git!**

## 📁 File Structure
```
TestBot/
├── bot.py              # Main bot file
├── database.py         # Database operations
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (jangan commit!)
├── .gitignore         # Git ignore rules
├── README.md          # Dokumentasi ini
├── GEMINI_SETUP.md    # Dokumentasi Gemini (deprecated)
├── schedule.db        # SQLite database (auto-generated)
└── analytics.log      # Usage analytics (auto-generated)
```

## 🔧 Troubleshooting

### Bot tidak merespons
- Cek apakah `BOT_TOKEN` di `.env` sudah benar
- Pastikan bot di-mention atau reply pesannya
- Cek apakah channel masuk dalam `GROQ_ALLOWED_CHANNELS`

### AI error
- Cek `GROQ_API_KEY` di `.env`
- Pastikan API key masih valid
- Cek console log untuk error detail

### Rate limit hit
- Tunggu 3 detik sebelum bertanya lagi
- Ini normal behavior untuk prevent spam

## 📊 Analytics

Usage tracking tersimpan di `analytics.log`:
```
2026-02-11 10:30:45|123456789|ai_chat
2026-02-11 10:31:12|987654321|add_schedule
2026-02-11 10:32:05|123456789|add_reminder
```

Format: `timestamp|user_id|command_name`

## 🤝 Contributing

Untuk menambahkan fitur baru:
1. Fork repository ini
2. Buat branch baru (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 📄 License

Bot ini dibuat untuk keperluan internal mahasiswa IS 1.

## 👥 Credits

Developed with ❤️ for IS 1 batch

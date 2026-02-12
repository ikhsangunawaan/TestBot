# IS 1 Assistant Bot 🤖

Discord bot asisten untuk mahasiswa Sistem Informasi IS 1 dengan AI chatbot (Groq), manajemen jadwal kuliah, dan reminder pribadi.

## ✨ Fitur Utama

### 🤖 AI Chatbot dengan Personality System
- Powered by Groq (llama-3.1-8b-instant)
- **5 Personality Profiles** yang bisa dipilih per user:
  - 😊 Teman Baik - Ramah, ceria, santai
  - 💼 Asisten Profesional - Formal, informatif, fokus data
  - 📚 Tutor Edukatif - Menjelaskan konsep dengan detail
  - 🚀 Motivator Energik - Penuh semangat & motivasi
  - 🤝 Asisten Membantu - Fokus solusi praktis
- Auto-inject database context (tidak mengarang data)
- Rate limiting (3 detik cooldown) untuk prevent spam
- Rich presence: "Listening to IS ONLY ONE"

### 📅 Manajemen Jadwal
- Tambah jadwal kuliah via text command atau natural language
- Lihat jadwal per hari, per mata kuliah, atau semua
- Hapus jadwal berdasarkan mata kuliah
- Auto-announcement jadwal harian
- Slash commands untuk admin (tambah/hapus/clear)

### ⏰ Reminder Pribadi
- Buat reminder dengan format fleksibel (1h30m, 2d, 45m) atau natural language
- Notifikasi via DM saat reminder tiba
- Auto-delete dari database setelah terkirim
- Lihat daftar reminder aktif
- Hapus semua reminder sekaligus

### 📊 Logging System
- Beautiful Discord embed logs
- Color-coded by event type (success, error, warning, reminder)
- Real-time tracking ke dedicated log channel
- Detailed information per event

### 🔐 Security & Privacy
- **Sensitive data filter** - Bot menolak menyimpan data sensitif seperti:
  - Password, PIN, OTP
  - KTP, NIK, NPWP
  - Kartu kredit, CVV, rekening
  - API keys, tokens, private keys
- Channel restriction untuk AI chat
- Admin-only commands
- Timezone support: Jakarta (WIB/UTC+7)

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

### 🎭 AI Personality Commands
| Command | Deskripsi | Contoh |
|---------|-----------|--------|
| `/personality` | Lihat semua personality AI yang tersedia | `/personality` |
| `/set_personality [id]` | Pilih personality favoritmu | `/set_personality tutor` |
| `/my_personality` | Lihat personality kamu yang sekarang | `/my_personality` |

**Available Personalities:**
- `friendly` - 😊 Teman Baik (default)
- `professional` - 💼 Asisten Profesional
- `tutor` - 📚 Tutor Edukatif
- `energik` - 🚀 Motivator Energik
- `helpful` - 🤝 Asisten Membantu

---

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

**View Reminders:**
```
"cek reminder"
"lihat reminder saya"
"daftar reminder"
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

**View Schedule:**
```
"jadwal hari ini"
"jadwal senin"
"cari jadwal AI"
"jadwal semua"
```

---

### 💬 Text Commands (Traditional Format)
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

---

### ⚡ Slash Commands (User)
| Command | Deskripsi |
|---------|-----------|
| `/personality` | Lihat semua personality AI |
| `/set_personality [id]` | Pilih personality favoritmu |
| `/my_personality` | Lihat personality kamu sekarang |
| `/isschedule [hari]` | Lihat jadwal kuliah |
| `/isremind` | Pasang reminder (via form) |
| `/ishelp` | Daftar perintah lengkap |
| `/ping` | Cek latensi bot |

---

### 🔑 Admin Commands
| Command | Deskripsi |
|---------|-----------|
| `/isinfo [pesan]` | Kirim pengumuman dengan tag role |
| `/isaddschedule` | Tambah jadwal (via form) |
| `/isremovetime [hari] [jam]` | Hapus jadwal jam tertentu |
| `/isclearschedule [hari]` | Hapus semua jadwal di hari tertentu |
| `/isannounce` | Kirim pesan ke channel lain (via form) |

## 💬 Cara Menggunakan AI Chat

### 1. Pilih Personality (Opsional)
Setiap user bisa pilih personality AI sesuai preferensi:
```
/personality                    # Lihat semua yang tersedia
/set_personality tutor          # Pilih personality
/my_personality                 # Cek personality sekarang
```

### 2. Chat dengan Bot
**Mention bot** di channel yang diizinkan:
```
@IS 1 Assistant Apa itu algoritma?
```

**Reply pesan bot** untuk melanjutkan percakapan:
```
[reply ke bot] Jelaskan lebih detail dong
```

**Tanya tentang jadwal/reminder:**
```
@IS 1 Assistant Ada jadwal apa hari ini?
@IS 1 Assistant Apa reminder aku yang aktif?
```

### 3. Personality akan membentuk response style
- **😊 Teman Baik**: Santai, friendly, pakai emoji
- **💼 Profesional**: Terstruktur, formal, poin-poin
- **📚 Tutor**: Penjelasan detail dengan contoh & analogi
- **🚀 Energik**: Motivatif, semangat, banyak emoji
- **🤝 Helpful**: Fokus solusi, actionable steps

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
├── bot.py              # Main bot file (1045 lines)
├── database.py         # Database operations (197 lines)
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (jangan commit!)
├── .gitignore         # Git ignore rules
├── README.md          # Dokumentasi ini
├── schedule.db        # SQLite database (auto-generated)
└── analytics.log      # Usage analytics (auto-generated)
```

## 🗄️ Database Schema

### Tables:
1. **schedule** - Jadwal kuliah
   - `day_of_week` (TEXT) - Hari kuliah
   - `time` (TEXT) - Jam kuliah (HH:MM)
   - `subject` (TEXT) - Nama mata kuliah

2. **reminders** - Reminder pribadi per user
   - `id` (INTEGER PRIMARY KEY) - ID reminder
   - `user_id` (INTEGER) - Discord user ID
   - `remind_at` (INTEGER) - Unix timestamp kapan reminder muncul
   - `message` (TEXT) - Pesan reminder

3. **personalities** - AI personality profiles
   - `id` (TEXT PRIMARY KEY) - Personality ID
   - `name` (TEXT) - Nama personality
   - `description` (TEXT) - Deskripsi singkat
   - `system_prompt` (TEXT) - System prompt untuk AI
   - `emoji` (TEXT) - Emoji representation

4. **user_personality** - User preference mapping
   - `user_id` (INTEGER PRIMARY KEY) - Discord user ID
   - `personality_id` (TEXT) - Preferred personality ID

## 🔧 Troubleshooting

### Bot tidak merespons
- Cek apakah `BOT_TOKEN` di `.env` sudah benar
- Pastikan bot di-mention atau reply pesannya
- Cek apakah channel masuk dalam `GROQ_ALLOWED_CHANNELS`

### AI error
- Cek `GROQ_API_KEY` di `.env`
- Pastikan API key masih valid
- Cek log channel untuk error detail

### Reminder tidak terkirim
- Pastikan user membuka DM dari bot
- Cek log channel untuk delivery status
- Reminder otomatis didelete setelah diproses (berhasil/gagal)

### Personality tidak berubah
- Pastikan personality ID valid (`friendly`, `professional`, `tutor`, `energik`, `helpful`)
- Gunakan `/my_personality` untuk verify
- Database menyimpan preference per user

### Rate limit hit
- Tunggu 3 detik sebelum bertanya lagi
- Ini normal behavior untuk prevent spam

### Timezone salah
- Bot menggunakan WIB (UTC+7)
- Semua timestamp di logs menggunakan WIB
- Reminder scheduling juga pakai WIB

## 📊 Analytics & Logging

### Analytics File (`analytics.log`)
Usage tracking tersimpan di `analytics.log`:
```
2026-02-12 12:30:45|123456789|ai_chat
2026-02-12 12:31:12|987654321|add_schedule
2026-02-12 12:32:05|123456789|add_reminder
```
Format: `timestamp|user_id|command_name`

### Discord Logging Channel
Bot mengirim real-time logs ke Discord channel (ID: `LOG_CHANNEL_ID`) dengan format embed:
- 🟢 **Success** (Green) - Reminder terkirim, operasi berhasil
- 🔴 **Error** (Red) - Gagal kirim DM, API error
- 🟡 **Reminder** (Yellow) - Reminder delivery events
- 🔵 **Info** (Blue) - General information
- 🟣 **Schedule** (Purple) - Schedule announcements
- 🟠 **Warning** (Orange) - User not found, non-critical issues

Semua logs include:
- Timestamp (WIB)
- Event title & description
- Relevant details (User ID, message, error type, etc.)
- Footer: "IS 1 Assistant Bot Logger"

## 🚀 Advanced Features

### 🎭 AI Personality System
Setiap user bisa customize pengalaman chatbot dengan memilih personality yang sesuai gaya belajar/komunikasi mereka. Bot menyimpan preference per user di database.

**5 Pre-configured Personalities:**
1. **Teman Baik** - Natural conversation, friendly tone
2. **Asisten Profesional** - Structured, formal, data-focused
3. **Tutor Edukatif** - Detailed explanations with examples
4. **Motivator Energik** - Enthusiastic, motivational messages
5. **Asisten Membantu** - Action-oriented, practical solutions

### 📊 Real-time Discord Logging
Semua bot activity (reminder delivery, errors, warnings) langsung terlog ke dedicated Discord channel dengan color-coded embeds untuk easy monitoring.

### 🕐 Timezone Support
Bot fully supports WIB (UTC+7) timezone untuk semua operasi:
- Reminder scheduling & delivery
- Schedule announcements
- Log timestamps
- Time display di commands

### 🔐 Security Features
- Sensitive data filtering (passwords, credentials, personal IDs)
- Rate limiting per user
- Channel restrictions
- Input validation untuk prevent injection

### 🤖 Smart Natural Language Processing
Bot mengerti berbagai format perintah:
- Time expressions: "dalam 5 menit", "2 jam lagi", "besok jam 10"
- Day names: Indonesia & English (Senin/Monday)
- Flexible phrasing: Bot extract intent dari natural sentences

---

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

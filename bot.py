try:
    import audioop
except ImportError:
    import sys
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

import asyncio
from datetime import datetime, timezone, timedelta
import os
import re
import time

import database
import discord
from groq import Groq
from discord import ui
from discord.ext import commands, tasks
from dotenv import load_dotenv

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()

# --- KONFIGURASI ---
# Timezone Jakarta (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_SERVERS = [1440333970091802665]
SCHEDULE_CHANNEL_ID = 1440355268138500107
ROLE_ID = "1440340102122307665"

# --- KONFIGURASI GROQ AI ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ALLOWED_CHANNELS = [1471130420857933937]
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_SYSTEM_PROMPT = os.getenv(
    "GROQ_SYSTEM_PROMPT",
    "Kamu adalah asisten friendly untuk mahasiswa Sistem Informasi IS 1 bernama IS 1 Assistant! "
    "Kamu ramah, ceria, perhatian, dan suka ngobrol santai dengan teman-teman IS 1. "
    "Kamu bisa jawab pertanyaan umum, diskusi topik kuliah, atau sekadar ngobrol. "
    "Jawab dengan natural dan enak dibaca, boleh pakai emoji sesekali. "
    "PENTING: Untuk data jadwal/reminder, HANYA gunakan data dari database yang diberikan. "
    "Jangan mengarang jadwal atau reminder yang tidak ada. Kalau tidak ada data, bilang terus terang. "
    "Tips: Ketik 'help' untuk lihat semua command yang tersedia!",
)
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "800"))

# Inisialisasi client di luar loop agar lebih efisien
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = discord.Bot(intents=intents)

database.init_db()

# Rate limiting untuk AI chat (cooldown per user)
user_cooldowns = {}
AI_COOLDOWN_SECONDS = 3

# Sensitive data keywords
SENSITIVE_KEYWORDS = [
    "password", "pwd", "pass", "kata sandi", "sandi",
    "pin", "ktp", "nik", "npwp", "rekening", "kartu kredit",
    "credit card", "cvv", "otp", "token api", "api key",
    "secret", "private key", "kunci"
]

INDO_TO_ENG = {
    "Senin": "monday",
    "Selasa": "tuesday",
    "Rabu": "wednesday",
    "Kamis": "thursday",
    "Jumat": "friday",
    "Sabtu": "saturday",
    "Minggu": "sunday",
}


def parse_duration_to_seconds(text):
    total_seconds = 0
    matches = re.findall(r"(\d+)\s*([dhms])", text.lower())
    for value, unit in matches:
        value_int = int(value)
        if unit == "d":
            total_seconds += value_int * 86400
        elif unit == "h":
            total_seconds += value_int * 3600
        elif unit == "m":
            total_seconds += value_int * 60
        elif unit == "s":
            total_seconds += value_int
    return total_seconds


def contains_sensitive_data(text):
    """Check if text contains sensitive keywords"""
    text_lower = text.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    return False, None


def log_command_usage(user_id, command_name):
    """Simple analytics tracking"""
    try:
        with open("analytics.log", "a", encoding="utf-8") as f:
            timestamp = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp}|{user_id}|{command_name}\n")
    except Exception as e:
        print(f"[ANALYTICS ERROR] {e}")

# --- TASKS ---

@tasks.loop(seconds=15)
async def check_reminders():
    due_reminders = database.get_due_reminders()
    for reminder_id, user_id, message in due_reminders:
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)
        if user:
            try:
                await user.send(f"⏰ **Reminder:** {message}")
            except discord.Forbidden:
                print(f"DM ditutup untuk user {user_id}")
        database.delete_reminder(reminder_id)

@tasks.loop(hours=24)
async def announce_schedule():
    await bot.wait_until_ready()
    channel = bot.get_channel(SCHEDULE_CHANNEL_ID)
    if channel:
        day_eng = datetime.now(WIB).strftime("%A").lower()
        schedule_data = database.get_schedule_for_day(day_eng)
        if schedule_data:
            embed = discord.Embed(
                title=f"📅 Jadwal Kuliah Hari Ini",
                color=discord.Color.blue(),
                timestamp=datetime.now(WIB),
            )
            for time_val, subject in schedule_data:
                embed.add_field(name=f"🕒 {time_val}", value=subject, inline=False)
            await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"--- IS 1 Assistant is Online! ---") # Tanda kehidupan di terminal
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    
    # Set rich presence
    activity = discord.Activity(type=discord.ActivityType.listening, name="IS ONLY ONE")
    await bot.change_presence(activity=activity, status=discord.Status.online)
    
    if not check_reminders.is_running():
        check_reminders.start()
    if not announce_schedule.is_running():
        announce_schedule.start()

@bot.event
async def on_message(message: discord.Message):
    """Handle mentions untuk Groq AI chatbot"""
    if message.author.bot:
        return

    # Check apakah bot di-mention atau pesan adalah reply ke bot
    is_mentioned = bot.user.mentioned_in(message)
    is_reply_to_bot = False
    if message.reference:
        ref_message = message.reference.resolved
        if ref_message is None:
            try:
                ref_message = await message.channel.fetch_message(message.reference.message_id)
            except discord.NotFound:
                ref_message = None
        if ref_message and ref_message.author.id == bot.user.id:
            is_reply_to_bot = True

    is_chatbot_channel = message.channel.id in GROQ_ALLOWED_CHANNELS

    # Jika ada batasan channel dan pesan bukan di channel tersebut
    if GROQ_ALLOWED_CHANNELS and not is_chatbot_channel:
        if is_mentioned or is_reply_to_bot:
            await message.reply("❌ Groq AI tidak diizinkan di channel ini.", mention_author=False)
        return

    if not (is_mentioned or is_reply_to_bot):
        await message.reply("Kamu perlu mention aku biar bisa jawab ya<3", mention_author=False)
        return

    if not GROQ_API_KEY or not client:
        await message.reply("❌ Groq API belum dikonfigurasi.", mention_author=False)
        return

    # Bersihkan pesan dari mention
    user_message = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

    if not user_message and is_mentioned:
        await message.reply("Halo! 👋 Ada yang bisa saya bantu? Coba tanya sesuatu.", mention_author=False)
        return
    elif not user_message:
        return

    schedule_add = re.match(
        r"(?i)^(tambah|add)\s+jadwal\s+(\w+)\s+(\d{1,2}:\d{2})\s+(.+)$",
        user_message,
    )
    if schedule_add:
        day_raw = schedule_add.group(2).strip().capitalize()
        time_val = schedule_add.group(3).strip()
        subject = schedule_add.group(4).strip()
        
        # Check sensitive data
        is_sensitive, keyword = contains_sensitive_data(subject)
        if is_sensitive:
            await message.reply(
                f"❌ Tidak dapat menyimpan data sensitif (terdeteksi: '{keyword}'). Jaga privasi kamu ya!",
                mention_author=False,
            )
            return
        
        if day_raw not in INDO_TO_ENG:
            await message.reply(
                "❌ Hari tidak valid. Gunakan: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu.",
                mention_author=False,
            )
            return
        database.add_schedule(INDO_TO_ENG[day_raw], time_val, subject)
        log_command_usage(message.author.id, "add_schedule")
        await message.reply(
            f"✅ Jadwal {day_raw} jam {time_val} berhasil ditambah.",
            mention_author=False,
        )
        return

    # Check untuk lihat semua jadwal
    if re.match(r"(?i)^(lihat|cek)?\s*jadwal\s+(semua|keseluruhan|lengkap)$", user_message):
        all_data = database.get_all_schedules()
        if not all_data:
            await message.reply("Belum ada jadwal tersimpan.", mention_author=False)
            return
        
        # Group by day
        from collections import defaultdict
        by_day = defaultdict(list)
        for day_eng, time_val, subject in all_data:
            day_name = [k for k, v in INDO_TO_ENG.items() if v == day_eng][0]
            by_day[day_name].append(f"  - {time_val} {subject}")
        
        lines = []
        for day in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
            if day in by_day:
                lines.append(f"**{day}:**")
                lines.extend(by_day[day])
        
        await message.reply(
            f"📅 Jadwal Lengkap:\n" + "\n".join(lines),
            mention_author=False,
        )
        return

    # Check untuk search by mata kuliah
    matkul_search = re.match(r"(?i)^jadwal\s+(.+)$", user_message)
    if matkul_search:
        query = matkul_search.group(1).strip()
        
        # Cek apakah query adalah hari
        day_query = query.capitalize()
        if day_query == "Hari ini":
            day_eng = datetime.now(WIB).strftime("%A").lower()
            day_name = [k for k, v in INDO_TO_ENG.items() if v == day_eng][0]
            data = database.get_schedule_for_day(day_eng)
            if not data:
                await message.reply(f"Gak ada jadwal buat hari {day_name}.", mention_author=False)
                return
            lines = [f"- {t_val} {sub}" for t_val, sub in data]
            await message.reply(
                f"📅 Jadwal {day_name}:\n" + "\n".join(lines),
                mention_author=False,
            )
            return
        elif day_query in INDO_TO_ENG:
            day_eng = INDO_TO_ENG[day_query]
            data = database.get_schedule_for_day(day_eng)
            if not data:
                await message.reply(f"Gak ada jadwal buat hari {day_query}.", mention_author=False)
                return
            lines = [f"- {t_val} {sub}" for t_val, sub in data]
            await message.reply(
                f"📅 Jadwal {day_query}:\n" + "\n".join(lines),
                mention_author=False,
            )
            return
        
        # Kalau bukan hari, cari by subject
        results = database.search_schedule_by_subject(query)
        if not results:
            await message.reply(
                f"Gak ada jadwal yang cocok dengan '{query}'.",
                mention_author=False,
            )
            return
        
        lines = []
        for day_eng, time_val, subject in results:
            day_name = [k for k, v in INDO_TO_ENG.items() if v == day_eng][0]
            lines.append(f"- {day_name} {time_val} | {subject}")
        
        await message.reply(
            f"📅 Jadwal '{query}':\n" + "\n".join(lines),
            mention_author=False,
        )
        return

    # Default: lihat jadwal hari ini
    if re.match(r"(?i)^(lihat|cek)?\s*jadwal$", user_message):
        day_eng = datetime.now(WIB).strftime("%A").lower()
        day_name = [k for k, v in INDO_TO_ENG.items() if v == day_eng][0]
        data = database.get_schedule_for_day(day_eng)
        if not data:
            await message.reply(f"Gak ada jadwal buat hari {day_name}.", mention_author=False)
            return
        lines = [f"- {t_val} {sub}" for t_val, sub in data]
        await message.reply(
            f"📅 Jadwal {day_name}:\n" + "\n".join(lines),
            mention_author=False,
        )
        return

    # Hapus jadwal by mata kuliah
    schedule_remove = re.match(
        r"(?i)^(hapus|delete|remove)\s+jadwal\s+(.+)$",
        user_message,
    )
    if schedule_remove:
        subject_query = schedule_remove.group(2).strip()
        results = database.search_schedule_by_subject(subject_query)
        if not results:
            await message.reply(
                f"❌ Tidak ada jadwal yang cocok dengan '{subject_query}'.",
                mention_author=False,
            )
            return
        
        # Hapus semua yang cocok
        count = database.delete_schedule_by_subject(subject_query)
        log_command_usage(message.author.id, "delete_schedule")
        await message.reply(
            f"✅ Berhasil menghapus {count} jadwal dengan kata kunci '{subject_query}'.",
            mention_author=False,
        )
        return

    reminder_add = re.match(
        r"(?i)^(tambah|add|buat|pasang)\s+reminder\s+(\S+)\s+(.+)$",
        user_message,
    )
    if not reminder_add:
        reminder_add = re.match(r"(?i)^ingatkan\s+(\S+)\s+(.+)$", user_message)

    if reminder_add:
        duration_str = reminder_add.group(2).strip()
        reminder_message = reminder_add.group(3).strip()
        
        # Check sensitive data
        is_sensitive, keyword = contains_sensitive_data(reminder_message)
        if is_sensitive:
            await message.reply(
                f"❌ Tidak dapat menyimpan data sensitif (terdeteksi: '{keyword}'). Jaga privasi kamu ya!",
                mention_author=False,
            )
            return
        
        seconds = parse_duration_to_seconds(duration_str)
        if seconds <= 0:
            await message.reply(
                "❌ Format waktu salah. Contoh: 1h30m, 2d, 45m, 10s.",
                mention_author=False,
            )
            return
        remind_at = int(time.time()) + seconds
        database.add_reminder(message.author.id, remind_at, reminder_message)
        log_command_usage(message.author.id, "add_reminder")
        await message.reply("✅ Reminder berhasil ditambahkan.", mention_author=False)
        return

    reminder_list = re.match(
        r"(?i)^(lihat|cek)\s+reminder(s)?(\s+saya)?$",
        user_message,
    )
    if reminder_list or user_message.lower() in {"reminder saya", "daftar reminder", "list reminder"}:
        reminders = database.get_user_reminders(message.author.id, limit=5)
        if not reminders:
            await message.reply("Belum ada reminder aktif.", mention_author=False)
            return
        lines = []
        for remind_at, reminder_message in reminders:
            time_str = datetime.datetime.fromtimestamp(remind_at).strftime("%d-%m %H:%M")
            lines.append(f"- {time_str} | {reminder_message}")
        await message.reply(
            "⏰ Reminder kamu:\n" + "\n".join(lines),
            mention_author=False,
        )
        return

    # Hapus semua reminder user
    reminder_delete = re.match(
        r"(?i)^(hapus|delete|clear)\s+(semua\s+)?reminder(s)?$",
        user_message,
    )
    if reminder_delete:
        count = database.delete_all_user_reminders(message.author.id)
        log_command_usage(message.author.id, "delete_reminders")
        if count > 0:
            await message.reply(
                f"✅ Berhasil menghapus {count} reminder.",
                mention_author=False,
            )
        else:
            await message.reply(
                "❌ Tidak ada reminder aktif untuk dihapus.",
                mention_author=False,
            )
        return

    # Jawab pertanyaan waktu secara deterministik
    time_pattern = r"\b(jam|pukul|waktu|time)\b"
    if re.search(time_pattern, user_message, re.IGNORECASE):
        now = datetime.now(WIB).strftime("%H:%M")
        await message.reply(f"Sekarang pukul {now} WIB.", mention_author=False)
        return

    # Help/Bantuan - berikan list command sesuai role user
    help_pattern = r"(?i)^(help|bantuan|perintah|command)(\s+(apa|yang|tersedia))?(\s+saja)?$"
    if re.match(help_pattern, user_message) or "bisa apa" in user_message.lower() or "command apa" in user_message.lower():
        is_admin = message.author.guild_permissions.administrator if message.guild else False
        
        help_text = "📖 **Perintah yang Bisa Kamu Gunakan**\n\n"
        
        # Text commands (semua user)
        help_text += "**📝 Text Commands (lewat chat):**\n"
        help_text += "• `tambah jadwal [Hari] [HH:MM] [Mata Kuliah]` - Tambah jadwal kuliah\n"
        help_text += "• `jadwal` - Lihat jadwal hari ini\n"
        help_text += "• `jadwal [Hari]` - Lihat jadwal hari tertentu (contoh: jadwal Senin)\n"
        help_text += "• `jadwal [Matkul]` - Cari jadwal mata kuliah (contoh: jadwal Matdis)\n"
        help_text += "• `jadwal semua` - Lihat semua jadwal\n"
        help_text += "• `hapus jadwal [Matkul]` - Hapus jadwal by mata kuliah\n"
        help_text += "• `tambah reminder [durasi] [pesan]` - Buat reminder (contoh: tambah reminder 1h30m belajar)\n"
        help_text += "• `lihat reminder` - Lihat reminder kamu\n"
        help_text += "• `hapus reminder` - Hapus semua reminder kamu\n"
        help_text += "• `jam` / `waktu` - Cek waktu sekarang\n"
        help_text += "• Tanya apa saja ke AI - Chat bebas dengan AI asisten IS 1\n\n"
        
        # Slash commands untuk semua user
        help_text += "**⚡ Slash Commands (untuk semua):**\n"
        help_text += "• `/isschedule [hari]` - Lihat jadwal kuliah\n"
        help_text += "• `/isremind` - Pasang reminder pribadi (via form)\n"
        help_text += "• `/ishelp` - Daftar perintah lengkap\n"
        help_text += "• `/ping` - Cek latensi bot\n\n"
        
        # Admin commands
        if is_admin:
            help_text += "**🔐 Admin Commands (khusus admin):**\n"
            help_text += "• `/isinfo [pesan]` - Kirim pengumuman dengan tag role SI-1\n"
            help_text += "• `/isaddschedule` - Tambah jadwal kuliah (via form)\n"
            help_text += "• `/isremovetime [hari] [jam]` - Hapus jadwal jam tertentu\n"
            help_text += "• `/isclearschedule [hari]` - Hapus semua jadwal di hari tertentu\n"
            help_text += "• `/isannounce` - Kirim pesan ke channel lain (via form)\n\n"
        
        help_text += "💡 **Tips:** Mention aku (@bot) atau reply pesan aku untuk chat!"
        
        await message.reply(help_text, mention_author=False)
        return

    # Rate limiting check
    user_id = message.author.id
    current_time = time.time()
    if user_id in user_cooldowns:
        time_since_last = current_time - user_cooldowns[user_id]
        if time_since_last < AI_COOLDOWN_SECONDS:
            remaining = AI_COOLDOWN_SECONDS - time_since_last
            await message.reply(
                f"⏳ Tunggu {remaining:.1f} detik sebelum bertanya lagi ya!",
                mention_author=False,
            )
            return
    
    user_cooldowns[user_id] = current_time

    async with message.channel.typing():
        try:
            # Log aktivitas ke terminal Azure kamu
            print(f"[LOG] {message.author} bertanya: {user_message}")
            log_command_usage(message.author.id, "ai_chat")

            # Inject database context untuk AI
            db_context = []
            
            # Ambil semua jadwal dari database
            all_schedules = database.get_all_schedules()
            if all_schedules:
                schedule_lines = []
                for day_eng, time_val, subject in all_schedules:
                    day_name = [k for k, v in INDO_TO_ENG.items() if v == day_eng][0]
                    schedule_lines.append(f"{day_name} {time_val}: {subject}")
                db_context.append(f"Jadwal kuliah yang tersimpan:\n" + "\n".join(schedule_lines))
            else:
                db_context.append("Jadwal kuliah: BELUM ADA (database kosong)")
            
            # Ambil reminder user
            user_reminders = database.get_user_reminders(message.author.id, limit=3)
            if user_reminders:
                reminder_lines = []
                for remind_at, reminder_msg in user_reminders:
                    time_str = datetime.datetime.fromtimestamp(remind_at).strftime("%d-%m %H:%M")
                    reminder_lines.append(f"{time_str}: {reminder_msg}")
                db_context.append(f"Reminder user ini:\n" + "\n".join(reminder_lines))
            else:
                db_context.append("Reminder user ini: BELUM ADA")
            
            context_message = "\n\n".join(db_context)

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": GROQ_SYSTEM_PROMPT},
                    {"role": "system", "content": f"[DATA DARI DATABASE]\n{context_message}"},
                    {"role": "user", "content": user_message},
                ],
            )
            ai_response = response.choices[0].message.content or ""

            if not ai_response:
                await message.reply("❌ Groq tidak mengembalikan respons.", mention_author=False)
                return

            # Split response jika > 2000 karakter
            if len(ai_response) > 2000:
                for i in range(0, len(ai_response), 2000):
                    await message.reply(ai_response[i:i+2000], mention_author=False)
            else:
                await message.reply(ai_response, mention_author=False)

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            await message.reply(f"❌ Error: {str(e)}", mention_author=False)


# --- MODALS (AnnounceModal, ScheduleModal, RemindModal tetap sama) ---
# ... (kode Modal kamu di sini) ...

# --- SLASH COMMANDS (isinfo, isaddschedule, dll tetap sama) ---
# ... (kode Slash Commands kamu di sini) ...

bot.run(BOT_TOKEN)
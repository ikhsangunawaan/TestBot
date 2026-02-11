try:
    import audioop
except ImportError:
    import sys
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

import asyncio
import datetime
import os
import re
import time

import database
import discord
import google.generativeai as genai
from discord import ui
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURASI ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_SERVERS = [1440333970091802665]
SCHEDULE_CHANNEL_ID = 1440355268138500107
ROLE_ID = "1440340102122307665"

# --- KONFIGURASI GEMINI AI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ALLOWED_CHANNELS = [1471130420857933937]

# Inisialisasi model di luar loop agar lebih efisien
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash") # Inisialisasi global

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = discord.Bot(intents=intents)

database.init_db()

INDO_TO_ENG = {
    "Senin": "monday",
    "Selasa": "tuesday",
    "Rabu": "wednesday",
    "Kamis": "thursday",
    "Jumat": "friday",
    "Sabtu": "saturday",
    "Minggu": "sunday",
}

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
        day_eng = datetime.datetime.now().strftime("%A").lower()
        schedule_data = database.get_schedule_for_day(day_eng)
        if schedule_data:
            embed = discord.Embed(
                title=f"📅 Jadwal Kuliah Hari Ini",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(),
            )
            for time_val, subject in schedule_data:
                embed.add_field(name=f"🕒 {time_val}", value=subject, inline=False)
            await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"--- IS 1 Assistant is Online! ---") # Tanda kehidupan di terminal
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    if not check_reminders.is_running():
        check_reminders.start()
    if not announce_schedule.is_running():
        announce_schedule.start()

@bot.event
async def on_message(message: discord.Message):
    """Handle mentions untuk Gemini AI chatbot"""
    if message.author.bot:
        return
    
    # Check apakah bot di-mention atau pesan di channel khusus chatbot tanpa mention
    # (Aku tambahkan logika channel ID juga biar lebih fleksibel)
    is_mentioned = bot.user.mentioned_in(message)
    is_chatbot_channel = message.channel.id in GEMINI_ALLOWED_CHANNELS

    if is_mentioned or (not GEMINI_ALLOWED_CHANNELS or is_chatbot_channel):
        # Jika ada batasan channel dan pesan bukan di channel tersebut
        if GEMINI_ALLOWED_CHANNELS and not is_chatbot_channel:
            if is_mentioned: # Hanya balas jika di-mention di channel salah
                await message.reply("❌ Gemini AI tidak diizinkan di channel ini.", mention_author=False)
            return
        
        if not GEMINI_API_KEY or not model:
            await message.reply("❌ Gemini API belum dikonfigurasi.", mention_author=False)
            return
        
        # Bersihkan pesan dari mention
        user_message = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not user_message and is_mentioned:
            await message.reply("Halo! 👋 Ada yang bisa saya bantu? Coba tanya sesuatu.", mention_author=False)
            return
        elif not user_message:
            return

        async with message.channel.typing():
            try:
                # Log aktivitas ke terminal Azure kamu
                print(f"[LOG] {message.author} bertanya: {user_message}") 
                
                response = model.generate_content(user_message)
                ai_response = response.text
                
                # Split response jika > 2000 karakter
                if len(ai_response) > 2000:
                    for i in range(0, len(ai_response), 2000):
                        await message.reply(ai_response[i:i+2000], mention_author=False)
                else:
                    await message.reply(ai_response, mention_author=False)
                    
            except Exception as e:
                print(f"[ERROR] {str(e)}")
                await message.reply(f"❌ Error: {str(e)}", mention_author=False)
    
    await bot.process_commands(message)

# --- MODALS (AnnounceModal, ScheduleModal, RemindModal tetap sama) ---
# ... (kode Modal kamu di sini) ...

# --- SLASH COMMANDS (isinfo, isaddschedule, dll tetap sama) ---
# ... (kode Slash Commands kamu di sini) ...

bot.run(BOT_TOKEN)
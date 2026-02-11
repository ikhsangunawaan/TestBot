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
# Masukkan ID Server kamu di sini
ALLOWED_SERVERS = [1440333970091802665]
# ID Channel tujuan pengumuman (info_si1)
SCHEDULE_CHANNEL_ID = 1440355268138500107
# ID Role SI-1 untuk tag otomatis
ROLE_ID = "1440340102122307665"

# --- KONFIGURASI GEMINI AI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Channel ID yang diizinkan untuk menggunakan Gemini AI (kosongkan [] untuk semua channel)
GEMINI_ALLOWED_CHANNELS = [1471130420857933937]
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = discord.Bot(intents=intents)

database.init_db()

# Mapping hari untuk sinkronisasi database
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
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    if not check_reminders.is_running():
        check_reminders.start()
    if not announce_schedule.is_running():
        announce_schedule.start()


@bot.event
async def on_message(message: discord.Message):
    """Handle mentions untuk Gemini AI chatbot"""
    # Jangan balas pesan dari bot sendiri
    if message.author.bot:
        return
    
    # Check apakah bot di-mention
    if bot.user.mentioned_in(message):
        # Check channel permission
        if GEMINI_ALLOWED_CHANNELS and message.channel.id not in GEMINI_ALLOWED_CHANNELS:
            await message.reply(
                "❌ Gemini AI tidak diizinkan di channel ini.",
                mention_author=False
            )
            return
        
        # Check apakah GEMINI_API_KEY tersedia
        if not GEMINI_API_KEY:
            await message.reply(
                "❌ Gemini API belum dikonfigurasi.",
                mention_author=False
            )
            return
        
        # Hapus mention dari pesan
        user_message = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not user_message:
            await message.reply(
                "Halo! 👋 Ada yang bisa saya bantu? Coba tanya sesuatu.",
                mention_author=False
            )
            return
        
        # Show typing indicator
        async with message.channel.typing():
            try:
                # Call Gemini API
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(user_message)
                
                # Ambil text response
                ai_response = response.text
                
                # Split response jika terlalu panjang (Discord limit 2000 chars)
                if len(ai_response) > 2000:
                    chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                    for chunk in chunks:
                        await message.reply(chunk, mention_author=False)
                else:
                    await message.reply(ai_response, mention_author=False)
                    
            except Exception as e:
                await message.reply(
                    f"❌ Error: {str(e)}",
                    mention_author=False
                )
    
    # Process commands
    await bot.process_commands(message)


# --- MODALS ---


class AnnounceModal(ui.Modal):
    def __init__(self, title="Buat Pengumuman Kustom") -> None:
        super().__init__(title=title)
        self.add_item(
            ui.InputText(label="Channel ID", placeholder="Masukkan ID channel...")
        )
        self.add_item(
            ui.InputText(
                label="Pesan",
                style=discord.InputTextStyle.paragraph,
                placeholder="Isi pengumuman...",
            )
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Check if user is administrator
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Hanya admin yang bisa menggunakan fitur ini.", ephemeral=True
                )
                return
            
            target_id = int(self.children[0].value)
            channel = interaction.guild.get_channel(target_id)
            if channel:
                await channel.send(self.children[1].value)
                await interaction.response.send_message(
                    f"✅ Terkirim ke {channel.mention}", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Channel tidak ditemukan.", ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "❌ Channel ID harus berupa angka.", ephemeral=True
            )
        except:
            await interaction.response.send_message(
                "❌ Terjadi kesalahan.", ephemeral=True
            )


class ScheduleModal(ui.Modal):
    def __init__(self, title="Tambah Jadwal Kuliah") -> None:
        super().__init__(title=title)
        self.add_item(
            ui.InputText(label="Hari", placeholder="Contoh: Senin, Selasa...")
        )
        self.add_item(ui.InputText(label="Jam", placeholder="Contoh: 09:00"))
        self.add_item(
            ui.InputText(label="Mata Kuliah", style=discord.InputTextStyle.paragraph)
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            day_raw = self.children[0].value.strip().capitalize()
            time_val = self.children[1].value.strip()
            subject = self.children[2].value.strip()
            
            if day_raw not in INDO_TO_ENG:
                await interaction.response.send_message(
                    f"❌ Hari '{day_raw}' tidak valid. Gunakan: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu",
                    ephemeral=True,
                )
                return
            
            day_eng = INDO_TO_ENG[day_raw]
            database.add_schedule(day_eng, time_val, subject)
            await interaction.response.send_message(
                f"✅ Jadwal {day_raw} jam {time_val} berhasil ditambah!",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Terjadi kesalahan: {str(e)}",
                ephemeral=True,
            )


class RemindModal(ui.Modal):
    def __init__(self, title="Pasang Pengingat") -> None:
        super().__init__(title=title)
        self.add_item(
            ui.InputText(
                label="Waktu (contoh: 1h30m)",
                placeholder="d=hari, h=jam, m=menit, s=detik",
            )
        )
        self.add_item(
            ui.InputText(label="Pesan Reminder", style=discord.InputTextStyle.paragraph)
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            seconds = 0
            t = self.children[0].value.strip().lower()
            message = self.children[1].value.strip()
            
            if not message:
                await interaction.response.send_message(
                    "❌ Pesan reminder tidak boleh kosong.", ephemeral=True
                )
                return
            
            d = re.search(r"(\d+)d", t)
            h = re.search(r"(\d+)h", t)
            m = re.search(r"(\d+)m", t)
            s = re.search(r"(\d+)s", t)
            
            if d:
                seconds += int(d.group(1)) * 86400
            if h:
                seconds += int(h.group(1)) * 3600
            if m:
                seconds += int(m.group(1)) * 60
            if s:
                seconds += int(s.group(1))
            
            if seconds == 0:
                await interaction.response.send_message(
                    "❌ Format waktu salah. Gunakan format: 1d, 2h, 30m, 15s (contoh: 1h30m)", ephemeral=True
                )
                return
            
            remind_at = int(time.time()) + seconds
            database.add_reminder(
                interaction.user.id, remind_at, message
            )
            await interaction.response.send_message(
                f"✅ Oke Igun, nanti aku DM ya!", ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Format waktu tidak valid. Gunakan angka untuk setiap unit (contoh: 1h30m).", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error: {str(e)}", ephemeral=True
            )


# --- SLASH COMMANDS ---


@bot.slash_command(
    name="isinfo",
    description="Kirim pengumuman dengan tag role SI-1",
    guild_ids=ALLOWED_SERVERS,
)
@commands.has_permissions(administrator=True)
async def isinfo(ctx, pesan: str):
    channel = bot.get_channel(SCHEDULE_CHANNEL_ID)
    if channel:
        pesan_rapi = pesan.replace("|", "\n")
        await channel.send(f"<@&{ROLE_ID}>")
        embed = discord.Embed(
            title="📢 Pengumuman SI-1",
            description=pesan_rapi,
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Admin: {ctx.author.display_name}")
        await channel.send(embed=embed)
        await ctx.respond("✅ Terkirim dengan tag Role!", ephemeral=True)


@bot.slash_command(
    name="isaddschedule", description="Tambah jadwal kuliah", guild_ids=ALLOWED_SERVERS
)
@commands.has_permissions(administrator=True)
async def isaddschedule(ctx):
    await ctx.send_modal(ScheduleModal())


@bot.slash_command(
    name="isremovetime",
    description="Hapus jadwal jam tertentu",
    guild_ids=ALLOWED_SERVERS,
)
@commands.has_permissions(administrator=True)
async def isremovetime(
    ctx,
    day: discord.Option(
        str, choices=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    ),
    time_val: discord.Option(str, "Jam (contoh: 09:00)"),
):
    day_eng = INDO_TO_ENG[day]
    deleted = database.remove_schedule(day_eng, time_val)
    msg = (
        f"✅ Jadwal {day} {time_val} dihapus!" if deleted > 0 else "❌ Data gak ketemu."
    )
    await ctx.respond(msg, ephemeral=True)


@bot.slash_command(
    name="isclearschedule",
    description="Hapus semua jadwal di hari tertentu",
    guild_ids=ALLOWED_SERVERS,
)
@commands.has_permissions(administrator=True)
async def isclearschedule(
    ctx,
    day: discord.Option(
        str, choices=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    ),
):
    day_eng = INDO_TO_ENG[day]
    count = database.clear_schedule(day_eng)
    await ctx.respond(
        f"✅ Berhasil menghapus {count} jadwal di hari {day}.", ephemeral=True
    )


@bot.slash_command(name="isschedule", description="Lihat jadwal kuliah")
async def isschedule(
    ctx,
    day: discord.Option(
        str,
        choices=["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"],
        required=False,
    ) = None,
):
    if day is None:
        day_eng = datetime.datetime.now().strftime("%A").lower()
        day_name = [k for k, v in INDO_TO_ENG.items() if v == day_eng][0].capitalize()
    else:
        day_eng = INDO_TO_ENG[day]
        day_name = day

    data = database.get_schedule_for_day(day_eng)
    if not data:
        await ctx.respond(f"Gak ada jadwal buat hari {day_name}.", ephemeral=True)
        return
    embed = discord.Embed(title=f"📅 Jadwal - {day_name}", color=discord.Color.blue())
    for t_val, sub in data:
        embed.add_field(name=f"🕒 {t_val}", value=sub, inline=False)
    await ctx.respond(embed=embed)


@bot.slash_command(name="ishelp", description="Daftar perintah asisten SI-1")
async def ishelp(ctx):
    embed = discord.Embed(title="📖 IS 1 Assistant Help", color=discord.Color.green())
    embed.add_field(
        name="Umum",
        value="`/isschedule` - Cek jadwal\n`/isremind` - Pasang reminder pribadi\n`/ping` - Tes respon",
        inline=False,
    )
    embed.add_field(
        name="Admin SI-1",
        value="`/isinfo` - Info cepat\n`/isaddschedule` - Tambah jadwal\n`/isremovetime` - Hapus jam tertentu\n`/isclearschedule` - Kosongkan satu hari\n`/isannounce` - Pesan ke channel lain",
        inline=False,
    )
    embed.add_field(
        name="🤖 AI Chatbot (Gemini)",
        value="Mention bot (cth: @IS 1 Assistant Apa itu Python?) untuk chat dengan Gemini AI\n*Catatan: Available di channel yang diizinkan saja*",
        inline=False,
    )
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="isremind", description="Pasang reminder pribadi")
async def isremind(ctx):
    await ctx.send_modal(RemindModal())


@bot.slash_command(
    name="isannounce",
    description="Kirim pengumuman ke channel lain",
    guild_ids=ALLOWED_SERVERS,
)
@commands.has_permissions(administrator=True)
async def isannounce(ctx):
    await ctx.send_modal(AnnounceModal())


@bot.slash_command(name="ping", description="Cek latensi")
async def ping(ctx):
    await ctx.respond(f"Pong! 🏓 ({round(bot.latency * 1000)}ms)")


bot.run(BOT_TOKEN)

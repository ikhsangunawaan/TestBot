#!/usr/bin/env python3
"""
Test Natural Language Processing untuk IS 1 Assistant Bot
Mendemonstrasikan bagaimana bot bisa memahami perintah dalam natural language.
"""

import re
from datetime import datetime, timezone, timedelta

# Timezone Jakarta (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))

INDO_TO_ENG = {
    "Senin": "monday",
    "Selasa": "tuesday",
    "Rabu": "wednesday",
    "Kamis": "thursday",
    "Jumat": "friday",
    "Sabtu": "saturday",
    "Minggu": "sunday",
}


def extract_duration_from_text(text):
    """Extract durasi dari text seperti 'dalam 5 menit', 'dalam 2 jam', dll"""
    duration_match = re.search(r"dalam\s+(\d+)\s*(menit|jam|hari|detik|m|h|d|s)", text, re.IGNORECASE)
    if duration_match:
        value = int(duration_match.group(1))
        unit = duration_match.group(2).lower()
        
        if unit in ["menit", "m"]:
            seconds = value * 60
        elif unit in ["jam", "h"]:
            seconds = value * 3600
        elif unit in ["hari", "d"]:
            seconds = value * 86400
        elif unit in ["detik", "s"]:
            seconds = value
        else:
            seconds = value * 60
        
        cleaned = re.sub(r"dalam\s+\d+\s*(menit|jam|hari|detik|m|h|d|s)", "", text, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^(untuk|apa|untuk apa|apa)\s*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        return seconds, cleaned
    
    return None, text


def extract_day_from_text(text):
    """Extract nama hari dari text"""
    day_patterns = [
        (r"\b(senin|monday|mon)\b", "monday", "Senin"),
        (r"\b(selasa|tuesday|tue)\b", "tuesday", "Selasa"),
        (r"\b(rabu|wednesday|wed)\b", "wednesday", "Rabu"),
        (r"\b(kamis|thursday|thu)\b", "thursday", "Kamis"),
        (r"\b(jumat|friday|fri)\b", "friday", "Jumat"),
        (r"\b(sabtu|saturday|sat)\b", "saturday", "Sabtu"),
        (r"\b(minggu|sunday|sun)\b", "sunday", "Minggu"),
    ]
    
    for pattern, day_eng, day_indo in day_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return day_eng, day_indo
    
    return None, None


def extract_time_from_text(text):
    """Extract waktu (HH:MM) dari text"""
    time_match = re.search(r"(?:jam|pukul)?\s*(\d{1,2}):(\d{2})", text, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
    
    return None


def parse_add_reminder_natural(text):
    """Parse: 'ingatkan/reminder dalam 5 menit untuk [teks]'"""
    if not re.search(r"\b(ingatkan|reminder|remind|ingat|ingetin)\b", text, re.IGNORECASE):
        return None, None
    
    text_clean = re.sub(r"\b(ingatkan|reminder|remind|ingat|ingetin)\b\s*", "", text, flags=re.IGNORECASE).strip()
    
    duration_seconds, reminder_text = extract_duration_from_text(text_clean)
    
    if duration_seconds and reminder_text and len(reminder_text.strip()) > 0:
        return duration_seconds, reminder_text.strip()
    
    return None, None


def parse_add_schedule_natural(text):
    """Parse natural language: 'tambah/tambahkan jadwal [hari] [jam] [subject]'"""
    if not re.search(r"\b(tambah|tambahkan|add)\b.*\b(jadwal|schedule)\b", text, re.IGNORECASE):
        return None
    
    text_clean = re.sub(r"(tambah|tambahkan|add)\s+(jadwal|schedule)\s*", "", text, flags=re.IGNORECASE).strip()
    
    day_eng, day_indo = extract_day_from_text(text_clean)
    if not day_eng:
        return None
    
    time_val = extract_time_from_text(text_clean)
    if not time_val:
        return None
    
    subject = re.sub(r"\b(senin|selasa|rabu|kamis|jumat|sabtu|minggu|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", "", text_clean, flags=re.IGNORECASE).strip()
    subject = re.sub(r"(?:jam|pukul)?\s*\d{1,2}:\d{2}", "", subject).strip()
    
    if not subject:
        return None
    
    return day_eng, day_indo, time_val, subject


def parse_delete_reminder_natural(text):
    """Parse natural language: 'hapus reminder [teks/terbaru]'"""
    if not re.search(r"\b(hapus|delete|remove|clear)\b.*\b(reminder|reminders)\b", text, re.IGNORECASE):
        return None
    
    text_clean = re.sub(r"(hapus|delete|remove|clear)\s+(semua\s+)?(reminder|reminders)\s*", "", text, flags=re.IGNORECASE).strip()
    
    # Cek untuk "semua" SEBELUM remove dari text
    if re.search(r"\b(semua|all)\b", text, re.IGNORECASE):
        return "all"
    
    if re.search(r"\b(terbaru|latest|terakhir)\b", text_clean, re.IGNORECASE):
        return "latest"
    
    if text_clean:
        return text_clean
    
    return None


# ===== COMPREHENSIVE TESTS =====

def test_reminder_commands():
    print("\n" + "="*60)
    print("🧪 TEST: REMINDER NATURAL LANGUAGE COMMANDS")
    print("="*60)
    
    test_cases = [
        "ingatkan aku dalam 5 menit untuk belajar",
        "reminder dalam 2 jam untuk makan siang",
        "ingat aku dalam 30 detik untuk submit tugas",
        "dalam 1 hari ingetin aku untuk tidur",
        "ingatkan untuk mengerjakan tugas dalam 45 menit",
    ]
    
    for text in test_cases:
        dur, reminder_text = parse_add_reminder_natural(text)
        if dur and reminder_text:
            minutes = dur / 60
            print(f"\n✅ INPUT: '{text}'")
            print(f"   DURATION: {dur}s ({minutes:.1f} min)")
            print(f"   TEXT: '{reminder_text}'")
        else:
            print(f"\n❌ PARSE FAILED: '{text}'")


def test_delete_reminder_commands():
    print("\n" + "="*60)
    print("🧪 TEST: DELETE REMINDER NATURAL LANGUAGE COMMANDS")
    print("="*60)
    
    test_cases = [
        ("hapus reminder belajar", "belajar"),
        ("delete reminder terbaru", "latest"),
        ("hapus semua reminder", "all"),
        ("clear reminder makan", "makan"),
    ]
    
    for text, expected in test_cases:
        result = parse_delete_reminder_natural(text)
        status = "✅" if result == expected else "❌"
        print(f"\n{status} INPUT: '{text}'")
        print(f"   RESULT: '{result}' (expected: '{expected}')")


def test_schedule_commands():
    print("\n" + "="*60)
    print("🧪 TEST: SCHEDULE NATURAL LANGUAGE COMMANDS")
    print("="*60)
    
    test_cases = [
        "tambahkan jadwal senin jam 08:00 kuliah AI",
        "tambah jadwal rabu 14:30 pemrograman web",
        "add schedule jumat pukul 10:00 basis data",
        "jadwal kamis jam 15:00 proyek akhir",
        "jadwal selasa 13:00 kalkulus",
    ]
    
    for text in test_cases:
        result = parse_add_schedule_natural(text)
        if result:
            day_eng, day_indo, time_val, subject = result
            print(f"\n✅ INPUT: '{text}'")
            print(f"   DAY: {day_indo} ({day_eng})")
            print(f"   TIME: {time_val}")
            print(f"   SUBJECT: {subject}")
        else:
            print(f"\n❌ PARSE FAILED: '{text}'")


def test_edge_cases():
    print("\n" + "="*60)
    print("🧪 TEST: EDGE CASES & VARIATIONS")
    print("="*60)
    
    # Test different duration formats
    print("\n📅 Duration Format Variations:")
    durations = [
        "dalam 5 menit untuk test",
        "dalam 2 jam untuk meeting",
        "dalam 1 hari untuk deadline",
        "dalam 30s untuk quick remind",
    ]
    
    for text in durations:
        dur, reminder_text = parse_add_reminder_natural(text)
        if dur:
            print(f"✅ '{text}' -> {dur}s ({reminder_text})")
        else:
            print(f"❌ Failed: '{text}'")
    
    # Test schedule with different day names
    print("\n📅 Schedule Day Variations:")
    days = [
        "tambah jadwal Senin jam 09:00 kelas",
        "tambah jadwal Monday 09:00 class",  # English
        "jadwal rabu 14:00 lecture",
    ]
    
    for text in days:
        result = parse_add_schedule_natural(text)
        if result:
            day_eng, day_indo, time, subject = result
            print(f"✅ '{text}'")
            print(f"   -> {day_indo} {time} {subject}")
        else:
            print(f"❌ Failed: '{text}'")


def test_summary():
    print("\n" + "="*60)
    print("📊 NATURAL LANGUAGE PROCESSING - SUMMARY")
    print("="*60)
    print("""
✅ SUPPORTED COMMANDS:

1️⃣ ADD REMINDER (Natural Language)
   - "ingatkan aku dalam 5 menit untuk belajar"
   - "reminder dalam 2 jam untuk makan"
   - Supports: menit, jam, hari, detik (atau m, h, d, s)

2️⃣ DELETE REMINDER (Natural Language)
   - "hapus reminder belajar" (delete by keyword)
   - "hapus reminder terbaru" (delete latest)
   - "hapus semua reminder" (delete all)

3️⃣ ADD SCHEDULE (Natural Language)
   - "tambahkan jadwal senin jam 08:00 kuliah AI"
   - "tambah jadwal rabu 14:30 pemrograman web"
   - Format: [tambah/add] jadwal [hari] [jam] [subject]

4️⃣ DELETE SCHEDULE (Natural Language)
   - "hapus jadwal senin jam 08:00"
   - Automatically finds and deletes the schedule

📌 KEY FEATURES:
   ✓ Case-insensitive parsing
   ✓ Flexible duration formats
   ✓ Support both Indonesian and English
   ✓ Smart text extraction
   ✓ No need for rigid command formats

🎯 BENEFITS:
   ✓ Feels more natural and conversational
   ✓ User can type like they're chatting
   ✓ Less cognitive load on remembering exact syntax
   ✓ Better UX for non-technical users
""")


if __name__ == "__main__":
    print("\n🚀 STARTING NATURAL LANGUAGE PROCESSING TESTS...")
    
    test_reminder_commands()
    test_delete_reminder_commands()
    test_schedule_commands()
    test_edge_cases()
    test_summary()
    
    print("\n" + "="*60)
    print("✨ ALL TESTS COMPLETED!")
    print("="*60 + "\n")

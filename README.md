# APK Renamer Bot 📦

Telegram bot jo APK ka naam badal kar wapas bhej deta hai. Pyrogram se bana hai.

## Bot kya karta hai

1. Tum APK file bhejte ho (private chat mein).
2. Bot original naam + size dikhata hai, aur 2 options deta hai:
   - **✏️ Custom Name** — apni marzi ka naam likho, bot us naam se APK bhej dega
     (naam mein `/ \ : * ? " < > |` allowed nahi — bot khud hata dega; `.apk` khud lag jayega).
   - **⚡ Automatic** — naam apne aap ban jayega:
     `OriginalName [Join @ratsontop].apk`
3. Renamed APK milne ke baad 2 options:
   - **🔄 Rename Again** — usi APK ko dobara naye naam se rename karo
   - **❌ Done** — khatam karo, temp files delete ho jayengi
4. **❌ Cancel** — beech mein cancel karo, temp files delete ho jayengi.
5. Sirf `.apk` files supported hain. Dusri file bhejoge to bot mana kar dega.
6. Bot sirf **owner** use kar sakta hai (private bot).

## Setup

### 1. Dependencies install karo

```bash
pip install -r requirements.txt
```

### 2. .env file banao

`.env.example` ko copy karke `.env` banao:

```bash
cp .env.example .env
```

Phir `.env` mein apni values bharo:

```
BOT_TOKEN=PASTE_YOUR_BOT_TOKEN
API_ID=PASTE_YOUR_API_ID
API_HASH=PASTE_YOUR_API_HASH
OWNER_ID=7966027018
```

- **BOT_TOKEN** — BotFather se mila hua token (is bot ka).
- **API_ID / API_HASH** — [my.telegram.org](https://my.telegram.org) se mile hue API credentials.
  (Agar `.env` mein ye khaali hain to bot Aand bot wali `.env` (`~/workspace/aand_bot/.env`) se API_ID/API_HASH le lega.)
- **OWNER_ID** — tumhari Telegram user ID (default: 7966027018). Sirf ye user bot use kar payega.

> ⚠️ Apna real `.env` kabhi GitHub par commit mat karo. Sirf `.env.example` share karo.

### 3. Bot chalao

```bash
python bot.py
```

Bot online hote hi Telegram par `/start` bhejo.

## Commands

| Command | Kaam |
|---------|------|
| `/start` | Welcome message + bot kaise use karein |
| `/help` | Short help text |

## Kaise use karein (user ke liye)

1. Bot ko APK file bhejo.
2. **Custom Name** dabao → naya naam likh kar bhejo, ya **Automatic** dabao.
3. Renamed APK mil jayega.
4. Dobara naam badalna ho to **Rename Again**, warna **Done**.

## Files

| File | Kaam |
|------|------|
| `bot.py` | Poora bot code (single file) |
| `requirements.txt` | Python dependencies |
| `README.md` | Ye guide |
| `.env.example` | Env variables ka sample (koi real value nahi) |

Temp APK files `./downloads/` folder mein save hoti hain aur Done/Cancel karne par delete ho jati hain.

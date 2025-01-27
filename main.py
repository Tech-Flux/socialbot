import os
import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp 
bot = telebot.TeleBot('5857831840:AAFmLrSTR3LspmMIUix__gqtIo31vFiBGdk')

conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()
ADMIN_ID = 1575316283
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    userid INTEGER PRIMARY KEY,
    username TEXT,
    premium BOOLEAN DEFAULT FALSE,
    coins INTEGER DEFAULT 1000,
    invited_by INTEGER
)
''')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    args = message.text.split()
    invited_by = None
    if len(args) > 1:
        try:
            invited_by = int(args[1])
        except ValueError:
            pass
    cursor.execute('SELECT * FROM users WHERE userid = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute('INSERT INTO users (userid, username, invited_by) VALUES (?, ?, ?)', (user_id, username, invited_by))
        conn.commit()
        if invited_by:
            cursor.execute('UPDATE users SET coins = coins + 100 WHERE userid = ?', (invited_by,))
            conn.commit()
            bot.send_message(invited_by, f'You received 100 coins because {username} joined using your invite link!')
        bot.send_message(message.chat.id, f'Welcome, {username}! You have been registered and received 1000 coins.')
    else:
        bot.send_message(message.chat.id, f'Welcome back, {username}!')
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton('My Profile', callback_data='profile'))
    menu.add(InlineKeyboardButton('Check Coins', callback_data='check_coins'))
    menu.add(InlineKeyboardButton('Upgrade Premium', callback_data='upgrade_premium'))
    menu.add(InlineKeyboardButton('Invite Friends', callback_data='invite'))
    bot.send_message(message.chat.id, 'Please choose an option:', reply_markup=menu)

@bot.message_handler(commands=['del'])
def delete_account(message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE userid = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute('DELETE FROM users WHERE userid = ?', (user_id,))
        conn.commit()
        bot.send_message(message.chat.id, 'Your account and all associated data have been deleted.')
    else:
        bot.send_message(message.chat.id, 'No account found to delete.')

@bot.message_handler(commands=['addprem'])
def add_premium(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'You do not have permission to execute this command.')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, 'Usage: /addprem <user_id>')
        return
    
    try:
        user_id = int(args[1])
        cursor.execute('SELECT * FROM users WHERE userid = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            cursor.execute('UPDATE users SET premium = TRUE WHERE userid = ?', (user_id,))
            conn.commit()
            bot.send_message(message.chat.id, f'User with ID {user_id} has been upgraded to premium.')
        else:
            bot.send_message(message.chat.id, f'No user found with ID {user_id}.')
    except ValueError:
        bot.send_message(message.chat.id, 'Please provide a valid user ID.')

@bot.message_handler(commands=['delprem'])
def remove_premium(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'You do not have permission to execute this command.')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, 'Usage: /delprem <user_id>')
        return

    try:
        user_id = int(args[1])
        cursor.execute('SELECT * FROM users WHERE userid = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            cursor.execute('UPDATE users SET premium = FALSE WHERE userid = ?', (user_id,))
            conn.commit()
            bot.send_message(message.chat.id, f'Premium status for user with ID {user_id} has been removed.')
        else:
            bot.send_message(message.chat.id, f'No user found with ID {user_id}.')
    except ValueError:
        bot.send_message(message.chat.id, 'Please provide a valid user ID.')

@bot.message_handler(commands=['id'])
def send_user_id(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"Your User ID is: {user_id}")



video_requests = {}

@bot.message_handler(commands=['download'])
def download_video(message):
    user_id = message.from_user.id
    username = message.from_user.first_name

    cursor.execute('SELECT * FROM users WHERE userid = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('INSERT INTO users (userid, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        bot.send_message(message.chat.id, f'Welcome, {username}! You have been registered and received 1000 coins.')

    bot.send_message(message.chat.id, 'Please send the YouTube URL of the video you want to download.')

@bot.message_handler(func=lambda message: True)
def fetch_video_formats(message):
    user_id = message.from_user.id
    video_url = message.text.strip()

    video_requests[user_id] = video_url

    cursor.execute('SELECT premium, coins FROM users WHERE userid = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        bot.send_message(message.chat.id, 'User not found in the database!')
        return

    premium, coins = user

    if not premium and coins < 200:
        bot.send_message(message.chat.id, 'You do not have enough coins to download this video. Please upgrade to premium.')
        return

    try:
        with yt_dlp.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            
            if not formats:
                bot.send_message(message.chat.id, 'No formats available for this video.')
                return
            
            formats = sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True)

            markup = InlineKeyboardMarkup()
            for fmt in formats[:4]:
                resolution = fmt.get('height', 'Audio-only')
                button = InlineKeyboardButton(f"{resolution}p 🎥", callback_data=f"download:{fmt['format_id']}")
                markup.add(button)
            
            bot.send_message(message.chat.id, 'Choose a resolution to download:', reply_markup=markup)

    except yt_dlp.utils.DownloadError as e:
        bot.send_message(message.chat.id, 'Error: Unable to process the video URL. Please try again with a different URL.')

@bot.callback_query_handler(func=lambda call: call.data.startswith("download:"))
def handle_download(call):
    print("Callback data received:", call.data)  # Debugging
    video_format_id = call.data.split(":")[1]
    print("Selected format ID:", video_format_id)  # Debugging

    video_url = video_requests.get(call.from_user.id)

    if not video_url:
        print("Video URL is missing for user:", call.from_user.id)  # Debugging
        bot.send_message(call.message.chat.id, "Video URL not found. Please try again.")
        return

    bot.answer_callback_query(call.id, "Downloading your video...")

    def progress_hook(d):
        if d['status'] == 'downloading':
            progress = d.get('_percent_str', '0%').strip()

            # Store the previous progress to avoid sending the same message
            if not hasattr(progress_hook, 'last_progress'):
                progress_hook.last_progress = ""

            # Only update the message if progress has changed
            if progress != progress_hook.last_progress:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"Downloading... {progress}"
                )
                progress_hook.last_progress = progress


    ydl_opts = {
        'format': video_format_id,
        'outtmpl': f"{call.from_user.id}_%(title)s.%(ext)s",
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video_file:
            bot.send_video(call.message.chat.id, video_file)

        cursor.execute('SELECT premium FROM users WHERE userid = ?', (call.from_user.id,))
        premium = cursor.fetchone()[0]

        if not premium:
            cursor.execute('UPDATE users SET coins = coins - 200 WHERE userid = ?', (call.from_user.id,))
            conn.commit()

        bot.send_message(call.message.chat.id, "Download complete!")
        os.remove(filename)

    except yt_dlp.utils.DownloadError as e:
        print("Download error:", e)  # Debugging
        bot.send_message(call.message.chat.id, f"Download error: {e}")
    except Exception as e:
        print("Unexpected error:", e)  # Debugging
        bot.send_message(call.message.chat.id, f"An error occurred: {e}")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.send_message(message.chat.id, 'Cannot process this command. Please use /start.')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'profile':
        cursor.execute('SELECT username, premium, coins FROM users WHERE userid = ?', (call.from_user.id,))
        user = cursor.fetchone()
        if user:
            username, premium, coins = user
            premium_status = "Yes" if premium else "No"
            bot.send_message(call.message.chat.id, f'Username: {username}\nPremium: {premium_status}\nCoins: {coins}')
    elif call.data == 'check_coins':
        cursor.execute('SELECT coins FROM users WHERE userid = ?', (call.from_user.id,))
        user = cursor.fetchone()
        if user:
            coins = user[0]
            bot.send_message(call.message.chat.id, f'You have {coins} coins.')
    elif call.data == 'upgrade_premium':
        #cursor.execute('UPDATE users SET premium = TRUE WHERE userid = ?', (call.from_user.id,))
        #conn.commit()
        bot.send_message(call.message.chat.id, '*If you want to buy premium, please make payment through the miniapp then send your Screenshot and ID `/id` to admin [\\@abdulmods]*',
        parse_mode='MarkdownV2'
      )
    elif call.data == 'invite':
        invite_link = f"https://t.me/abdullahirahbot?start={call.from_user.id}"
        bot.send_message(call.message.chat.id, f"Share this invite link with your friends:\n{invite_link}\n\nYou'll get 100 coins for every friend who joins using your link!")

bot.polling(none_stop=True)


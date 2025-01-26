import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('5857831840:AAFmLrSTR3LspmMIUix__gqtIo31vFiBGdk')

conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()
USER_ID = 1575316283
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
    args = message.text.split()
    if len(args) != 2 and user.id == USER_ID:
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


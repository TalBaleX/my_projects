import telebot
import sqlite3
import os
from research import fetch_news_by_tag
from telebot import formatting
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

bot = telebot.TeleBot(os.getenv("TOKEN"), parse_mode='HTML')

def init_db():
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY,
        hashtags TEXT
    )
    ''')
    connection.commit()
    connection.close()

init_db()

def get_user_interests(chat_id):
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT hashtags FROM Users WHERE id = ?', (chat_id,))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result and result[0] else None

def set_hashtags(bot, message):
    chat_id = message.chat.id
    try:
        connection = sqlite3.connect('my_database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT hashtags FROM Users WHERE id = ?', (chat_id,))
        result = cursor.fetchone()
        current_hashtags = result[0] if result else "No hashtags saved yet"
        bot.send_message(
            chat_id,
            f"Your current interests:\n{current_hashtags}\n\n"
            "Please send me new topics that interest you with hashtags, separated by commas\n"
            "(Example: #python, #ai, #coding)"
        )
        bot.register_next_step_handler(message, lambda msg: save_hashtags(bot, msg))
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred while fetching your current interests: {str(e)}")
    finally:
        connection.close()

def save_hashtags(bot, message):
    chat_id = message.chat.id
    hashtags = message.text
    if hashtags == "/start":
        greet(message)
        return
    try:
        connection = sqlite3.connect('my_database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM Users WHERE id = ?', (chat_id,))
        if cursor.fetchone():
            cursor.execute('UPDATE Users SET hashtags = ? WHERE id = ?', (hashtags, chat_id))
        else:
            cursor.execute('INSERT INTO Users (id, hashtags) VALUES (?, ?)', (chat_id, hashtags))
        connection.commit()
        bot.send_message(chat_id, f"Your interests have been updated successfully!\nNew interests: {hashtags}")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred while saving your interests: {str(e)}")
    finally:
        connection.close()

@bot.message_handler(commands=['start'])
def greet(message):
    user_first_name = str(message.chat.first_name)
    chat_id = message.chat.id
    current_interests = get_user_interests(chat_id)
    interests_text = current_interests if current_interests else 'No interests set yet'
    bot.reply_to(message, formatting.hbold(f"Hey, {user_first_name}! 👋") +
        f" I'm 'Baking News' bot 🤖 I am here to notify you about everything what happens in the world 😊\n\n" +
        f"Would you like to see what's interesting today? (Your interests: {interests_text})")
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(KeyboardButton('Set Preferences'), KeyboardButton('Start Exploration'))
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=reply_markup)
    bot.register_next_step_handler(message, handle_choice)

def handle_choice(message):
    chat_id = message.chat.id
    current_interests = get_user_interests(chat_id)
    if message.text == "/start":
        greet(message)
        return
    elif message.text == "Set Preferences":
        set_hashtags(bot, message)
    elif message.text == "Start Exploration":
        if not current_interests:
            bot.send_message(chat_id, "You have not set any interests yet. Please set your preferences first!")
            set_hashtags(bot, message)
        else:
            bot.send_message(chat_id, f"Here's what's interesting today for you! (Interests: {current_interests})")
            fetch_news_by_tag(current_interests)

if __name__ == "__main__":
    bot.infinity_polling()


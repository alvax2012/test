import telebot
import requests
import time

from bs4 import BeautifulSoup

token = "7161260879:AAH9yJB6eAFjA2rFa9jMySptbWTLWvihtow" # Ваш токен
channel_id = "-1002133242685" # Ваш логин канала
# channel_id = "@alv_204"
bot = telebot.TeleBot(token)

@bot.message_handler(content_types=['text'])
def commands(message):
    bot.send_message(channel_id, message.text)

bot.polling()
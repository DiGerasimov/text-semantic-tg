import logging
from multiprocessing import Process
from os import getenv
from typing import List, Callable, Optional

import telebot
from telebot.types import Message

from dotenv import load_dotenv

try:
    from neuron import summarize_with_return
except Exception as e:
    print("Can't import neuron:", e)

    def summarize_with_return(text: str):
        return '!! Converted: ' + text


load_dotenv()

MAX_SUBPROCESS = 1

API_TOKEN = getenv('TOKEN')

logging.basicConfig(level=logging.INFO)

queue_count = 0
queue: List[Callable] = []

bot = telebot.TeleBot(API_TOKEN)


def _process_convert(message: Message, message_to_delete: Optional[Message] = None):
    if message_to_delete:
        bot.delete_message(chat_id=message_to_delete.chat.id, message_id=message_to_delete.message_id)

    sent_message = bot.reply_to(message, 'Началась обработка вашего текста!')
    bot.reply_to(message, summarize_with_return(message.text))

    bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)

    if queue:
        del queue[0]

    if queue:
        queue[0]()


@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    bot.reply_to(message, 'Здравствуйте!\n'
                          'Отправьте текст для семантического анализа')


@bot.message_handler(func=lambda message: True)
def convert_message(message: Message):
    global queue

    if len(message.text) <= 80:
        return bot.reply_to(message, message.text)

    if len(queue) < MAX_SUBPROCESS:
        queue.append(lambda: _process_convert(message=message))
        p = Process(target=queue[-1])
        p.run()
    else:
        sent_message = bot.reply_to(
            message,
            'Обработка вашего текста скоро начнётся!\n'
            f'Место в очереди: {len(queue)}')

        queue.append(lambda: _process_convert(
            message=message, message_to_delete=sent_message
        ))


logging.info('Neuron was loaded successfully!')
bot.polling()

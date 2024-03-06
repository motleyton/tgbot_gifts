
import logging
import traceback

from telegram import Message, MessageEntity, Update
from telegram.ext import ContextTypes, CallbackContext


async def error_handler(self, update: Update, context: CallbackContext, error_message: str):
    # Логгирование ошибки для отладки
    print(f"Произошла ошибка: {error_message}")

    # Отправка сообщения с извинениями и перезапуск команды start
    await update.message.reply_text("Извините, произошла ошибка. Попробуем начать сначала.")
    await self.start(update, context)

def message_text(message: Message) -> str:
    """
    Returns the text of a message, excluding any bot commands.
    """
    message_txt = message.text
    if message_txt is None:
        return ''

    for _, text in sorted(message.parse_entities([MessageEntity.BOT_COMMAND]).items(),
                          key=(lambda item: item[0].offset)):
        message_txt = message_txt.replace(text, '').strip()

    return message_txt if len(message_txt) > 0 else ''

def get_thread_id(update: Update) -> int | None:
    """
    Gets the message thread id for the update, if any
    """
    if update.effective_message and update.effective_message.is_topic_message:
        return update.effective_message.message_thread_id
    return None
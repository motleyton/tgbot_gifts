from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, CallbackContext

import logging

from openai_helper import OpenAIClient
from tools import *
# Настройка логирования
logging.basicConfig(level=logging.INFO)

class GiftBot:
    """Telegram bot for managing birthdays."""
    # Конструктор и метод start остаются без изменений
    def __init__(self, config: dict, openai: OpenAIClient, google_search: GoogleSearchTool):
        self.config = config
        self.openai = openai
        self.google_search = google_search
    async def start(self, update: Update, context: CallbackContext) -> None:
        keyboard = [["⚽️ Спорт", "🏠 Товары для дома"], ["📱 Электроника", "🧸 Для детей"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            "Привет! Для начала, давай определимся с подарком. Пожалуйста, выбери категорию подарка.",
            reply_markup=reply_markup)

    async def handle_choice(self, update: Update, context: CallbackContext) -> None:
        choice = update.message.text
        # Определение промпта на основе выбора пользователя
        detailed_prompt = self.get_detailed_prompt(choice)

        # Генерация ответа с помощью OpenAI
        recommendations = self.openai.get_response(
            detailed_prompt)  # Убедитесь, что get_response теперь асинхронный

        # Выводим рекомендации и поиск соответствующих ссылок через Google CSE
        search_queries = self.google_search.parse_gpt_response(recommendations)
        message_texts = []  # Список для хранения строк сообщений
        for recommendation, query in zip(recommendations, search_queries):
            results = self.google_search.google_search(query)
            if results:
                # Берем только первый результат для каждого запроса
                result = results[0]
                print(result)
                message_texts.append(f"{recommendation} - [Ссылка]({result['link']})")
            else:
                message_texts.append(f"{recommendation} - Извините, по вашему запросу ничего не найдено.")

            # Формирование итогового сообщения
        final_message = "\n\n".join(message_texts)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_message, parse_mode='Markdown', disable_web_page_preview=True)



    def get_detailed_prompt(self, choice):
        prompts = {
            "⚽️ Спорт": "Придумай уникальные идеи подарков на тему спорта и затем дай краткое описание каждого. Бюджет до 5000 рублей. Пример: Спортивный рюкзак: С отделениями для обуви и влажных вещей, идеален для походов в спортзал.",
            "🏠 Товары для дома": "Придумай идеи подарков, которые улучшат дом или создадут уют, и затем дай краткое описание каждого. Бюджет до 5000 рублей. Пример: Умная лампочка: Позволяет регулировать освещение в доме с помощью смартфона, создавая уютную атмосферу.",
            "📱 Электроника": "Придумай подарки, связанные с электроникой и новыми технологиями, и затем дай краткое описание каждого. Пример: Беспроводные наушники: С высоким качеством звука и долгим временем работы, идеальны для любителей музыки и подкастов.",
            "🧸 Для детей": "Придумай идеи подарков для детей, которые будут образовательными и развлекательными, и затем дай краткое описание каждого. Пример: Обучающий робот: Помогает детям учиться программированию через игру, развивая логическое мышление и творческие способности."

            }

        return prompts.get(choice, "Извините, я не смог определить категорию. Пожалуйста, попробуйте ещё раз.")

    def run(self):
        """Runs the bot."""
        application = ApplicationBuilder() \
            .token(self.config['token']) \
            .build()

        category_filters = (
                filters.Regex(r'^⚽️ Спорт$') |
                filters.Regex(r'^🏠 Товары для дома$') |
                filters.Regex(r'^📱 Электроника$') |
                filters.Regex(r'^🧸 Для детей$')
        )
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(MessageHandler(filters.TEXT & category_filters, self.handle_choice))
        application.run_polling()
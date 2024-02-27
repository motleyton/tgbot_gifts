from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, ContextTypes, CallbackContext, ConversationHandler, CallbackQueryHandler

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
        recommendations =  self.openai.get_response(
            detailed_prompt)  # Убедитесь, что get_response теперь асинхронный

        # Выводим рекомендации и поиск соответствующих ссылок через Google CSE
        search_queries = self.google_search.parse_gpt_response(recommendations)
        message_texts = []  # Список для хранения строк сообщений
        for i, query in enumerate(search_queries, start=1):
            results = self.google_search.google_search(query)
            if results:
                # Берем только первый результат для каждого запроса
                result = results[0]
                message_texts.append(f"{i}. {query} - [Ссылка]({result['link']})")
            else:
                message_texts.append(f"{i}. {query} - Извините, по вашему запросу ничего не найдено.")

        # Объединяем все строки в одно сообщение
        final_message = "\n".join(message_texts)
        # Отправляем единое сообщение
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_message, parse_mode='Markdown')

    def get_detailed_prompt(self, choice):
        prompts = {
            "⚽️ Спорт": "Предложи уникальные и интересные идеи подарков для человека, который активно занимается спортом. Предлагай варианты без 'или'",
            "🏠 Товары для дома": "Предложи идеи подарков для улучшения дома или создания уюта. Предлагай варианты без 'или'.",
            "📱 Электроника": "Что можно подарить любителю электроники и новых технологий? Предлагай варианты без 'или' ",
            "🧸 Для детей": "Нужны идеи подарков для детей, которые будут как образовательными, так и развлекательными. Предлагай варианты без 'или' "
            
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
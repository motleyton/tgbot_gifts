from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, CallbackContext, CallbackQueryHandler

import logging

from openai_helper import OpenAIClient
from tools import *
from utils import error_handler

# Настройка логирования
logging.basicConfig(level=logging.INFO)

class GiftBot:
    def __init__(self, config: dict, openai: OpenAIClient, google_search: GoogleSearchTool):
        self.config = config
        self.openai = openai
        self.google_search = google_search
        self.error_handler = error_handler

    async def start(self, update: Update, context: CallbackContext) -> None:
        keyboard = [
            [InlineKeyboardButton("Мужской", callback_data='gender_male')],
            [InlineKeyboardButton("Женский", callback_data='gender_female')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Привет! Выберите пол', reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: CallbackContext) -> None:
        try:
            query = update.callback_query
            await query.answer()
            data = query.data

            if data.startswith('gender_'):
                context.user_data['gender'] = 'мужской' if data == 'gender_male' else 'женский'
                keyboard = [
                    [InlineKeyboardButton(f"{age} лет", callback_data=f'age_{age}') for age in
                     ['5-10', '10-15', '15-20', '20-25', '25-35', '35-45']],
                    [InlineKeyboardButton("Назад", callback_data='back_to_start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text='Выберите возрастную категорию:', reply_markup=reply_markup)

            elif data.startswith('age_'):
                context.user_data['age_range'] = data.split('_')[1]
                keyboard = [
                    [InlineKeyboardButton(category, callback_data=f'category_{category}') for category in
                     ['Спорт', 'Электроника', 'Для дома']],
                    [InlineKeyboardButton("Назад", callback_data='back_to_gender')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text='Выберите категорию подарка:', reply_markup=reply_markup)

            elif data == 'back_to_start':
                # Отправляем пользователя обратно к выбору пола
                keyboard = [
                    [InlineKeyboardButton("Мужской", callback_data='gender_male')],
                    [InlineKeyboardButton("Женский", callback_data='gender_female')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text('Выберите пол', reply_markup=reply_markup)

            elif data == 'back_to_gender':
                # Отправляем пользователя обратно к выбору возраста
                gender = context.user_data.get('gender',
                                               'мужской')  # Значение по умолчанию, на случай если что-то пошло не так
                keyboard = [
                    [InlineKeyboardButton(f"{age} лет", callback_data=f'age_{age}') for age in
                     ['5-10', '10-15', '15-20', '20-25', '25-35', '35-45']],
                    [InlineKeyboardButton("Назад", callback_data='back_to_start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text='Выберите возрастную категорию:', reply_markup=reply_markup)

            elif data == 'back_to_age':
                # Отправляем пользователя обратно к выбору возраста
                keyboard = [
                    [InlineKeyboardButton(f"{age} лет", callback_data=f'age_{age}') for age in
                     ['5-10', '10-15', '15-20', '20-25', '25-35', '35-45']],
                    [InlineKeyboardButton("Назад", callback_data='back_to_start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text='Выберите возрастную категорию:', reply_markup=reply_markup)

            elif data.startswith('category_'):
                category = data.split('_')[1]
                await self.handle_choice(update, context, category)

            elif data.startswith('retry_'):
                category = data.split('_')[1]
                await self.handle_choice(update, context, category)

            elif data == 'back_to_category':
                # Отправляем пользователя обратно к выбору категории
                age_range = context.user_data.get('age_range', '5-10')  # Значение по умолчанию на случай ошибки
                keyboard = [
                    [InlineKeyboardButton(category, callback_data=f'category_{category}') for category in
                     ['Спорт', 'Электроника', 'Для дома']],
                    [InlineKeyboardButton("Назад", callback_data='back_to_age')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text='Выберите категорию подарка:', reply_markup=reply_markup)
        except Exception as e:
            await self.error_handler(update, context, str(e))

    async def handle_choice(self, update: Update, context: CallbackContext, category: str) -> None:
        # Отправляем сообщение о том, что запрос обрабатывается
        try:
            await update.callback_query.edit_message_text(text='Запрос обрабатывается, подождите...')

            gender = context.user_data['gender']
            age_range = context.user_data['age_range']
            detailed_prompt = self.get_detailed_prompt(category, gender, age_range)

            recommendations = self.openai.get_response(detailed_prompt)
            search_queries = self.google_search.parse_gpt_response(recommendations)
            message_texts = []

            intro_message = (f"Вот идеи для подарков: \n"
                             f"Пол: {gender} \n"
                             f"Возрастная категория: {age_range}")
            message_texts.append(intro_message)

            for recommendation, query in zip(recommendations, search_queries):
                results = self.google_search.google_search(query)
                if results:
                    result = results[0]
                    message_texts.append(f"{recommendation} - [Ссылка]({result['link']})")
                else:
                    message_texts.append(f"{recommendation} - Извините, по вашему запросу ничего не найдено.")

            final_message = "\n\n".join(message_texts)
            keyboard = [
                [InlineKeyboardButton("Еще варианты", callback_data=f'retry_{category}')],
                [InlineKeyboardButton("Назад", callback_data='back_to_category')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text=final_message, reply_markup=reply_markup,
                                                          parse_mode='Markdown', disable_web_page_preview=True)

        except Exception as e:
            await self.error_handler(update, context, str(e))


    def get_detailed_prompt(self, category, gender, age_range):
        return (f"Пожалуйста, предложи идеи подарков для {gender} возраста {age_range} лет, которые соответствуют категории {category}. Учти интересы и возможные предпочтения этой возрастной группы."
                f"Генерируй только то, что относится к подаркам.")

    def run(self):
        """Runs the bot."""
        application = ApplicationBuilder().token(self.config['token']).build()
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.run_polling()

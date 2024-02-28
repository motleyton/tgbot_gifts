import logging
import os
import json
from typing import List

from openai import OpenAI

# Load translations
parent_dir_path = os.path.join(os.path.dirname(__file__), os.pardir)
translations_file_path = os.path.join(parent_dir_path, 'translations.json')
with open(translations_file_path, 'r', encoding='utf-8') as f:
    translations = json.load(f)

# Включение логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def localized_text(key, bot_language):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    try:
        return translations[bot_language][key]
    except KeyError:
        logging.warning(f"No translation available for bot_language code '{bot_language}' and key '{key}'")
        if key in translations['en']:
            return translations['en'][key]
        logging.warning(f"No english definition found for key '{key}' in translations.json")
        # return key as text
        return key


class OpenAIClient:
    def __init__(self, config: dict):
        """
        Initializes the OpenAI helper class with the given configuration.
        :param config: A dictionary containing the GPT configuration
        """
        self.openai_api_key = config['openai_api_key']
        self.config = config
        self.model_name = config['model']
        self.temperature = config['temperature']
        self.client = OpenAI(
            api_key=self.openai_api_key)

    def _create_prompt(self, prompt:str) -> list:
        """
        Creates a chat prompt for generating a birthday greeting including the name.
        """
        system_prompt = f"""
                You are a helpful assistant asked to provide gift recommendations. Gift budget 5 thousand rubles. 
         """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}

        ]
        return messages

    def get_response(self, prompt: str) -> List[str]:
        messages = self._create_prompt(prompt)
        responses = []  # Инициализация списка для хранения ответов

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )

            # Предполагаем, что модель возвращает один длинный текст
            if chat_completion.choices:
                full_response = chat_completion.choices[0].message.content  # Берём первый ответ

                # Разделяем ответ на отдельные рекомендации
                # Здесь предполагается, что каждая рекомендация отделена паттерном "\n\n"
                individual_responses = full_response.split("\n\n")

                # Фильтрация пустых строк и добавление в список ответов
                responses = [response.strip() for response in individual_responses if response.strip()]

            return responses if responses else ["Извините, не удалось получить ответ."]

        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса к GPT: {e}")
            return ["Произошла ошибка при обработке вашего запроса."]




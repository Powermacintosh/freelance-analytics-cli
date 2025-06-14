# -*- encoding: utf-8 -*-
import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings

load_dotenv()
BASE_DIR = Path(__file__).parent.parent


class LLMGroqConfiguration(BaseModel):
    model: str = 'llama3-70b-8192'
    base_url: str = 'https://api.groq.com/openai/v1'
    api_key: str = os.getenv('GROQ_API_KEY', '')

    BASE_PROMPT: str = (
        'Ты — ассистент, аналитик данных о фрилансерах.\n'
        'Твоя задача — понять какие данные пользователь хочет получить и вызвать соответствующую функцию (tool).\n'
        'Если для ответа на вопрос пользователя требуется вызвать несколько инструментов (tools), то используй функцию batch_analytics.\n'
        'Используй только инструменты для аналитики, даже если кажется, что ты знаешь ответ.\n'
        'За один раз можно вызывать только один инструмент (tool).\n'
        'Не вызывай несуществующие инструменты.\n'
        'Нельзя делать несколько отдельных вызовов инструментов подряд - нужно либо собрать их все в один batch_analytics, либо вызвать один конкретный инструмент.\n'
        'Когда пользователь спрашивает о доступных инструментах или метриках, ВСЕГДА перечисляй описание ВСЕХ доступных инструментов из списка ниже.\n'
        'Если пользователь просит сводный отчет, то вызывай инструмент batch_analytics и передавай в него все инструменты, которые ему нужны.\n'
        'И поскольку ты РУССКИЙ ассистент, веди диалог на РУССКОМ языке. Отвечай только на РУССКОМ языке.'
    )
    
    system_prompt: str = f'{BASE_PROMPT}'


class LLMGigaChatConfiguration(BaseModel):
    model: str = 'GigaChat-2-max'
    verify_ssl_certs: bool = False
    api_key: str = os.getenv('GIGACHAT_API_KEY', '')

    BASE_PROMPT: str = (
        'Ты — ассистент, аналитик данных о фрилансерах.\n'
        'Твоя задача — понять какие данные пользователь хочет получить и вызвать соответствующую функцию.\n'
        'Если для ответа на вопрос пользователя требуется вызвать несколько инструментов (tools), то используй функцию batch_analytics.\n'
        'Если вызываешь инструмент batch_analytics, то ВСЕГДА показывай пользователю ВСЕ полученные данные в том виде, в котором они пришли от инструмента, без агрегации и сокращений.\n'
        'За один раз можно вызывать только один инструмент (tool).\n'
        'Не вызывай несуществующие инструменты.\n'
        'Нельзя делать несколько отдельных вызовов инструментов подряд - нужно либо собрать их все в один batch_analytics, либо вызвать один конкретный инструмент.\n'
        'Когда пользователь спрашивает о доступных инструментах или метриках, ВСЕГДА перечисляй описание ВСЕХ доступных инструментов из списка ниже.\n'
        'Если пользователь просит сводный отчет, то вызывай инструмент batch_analytics и передавай в него все инструменты, которые ему нужны.\n'
    )

    METHODS_LIST: str = """
        Доступные методы для анализа:

        Методы без параметров:
            - crypto_vs_other_income
            - income_by_region
            - percent_experts_lt_100_projects
            - avg_income_by_category
            - avg_income_by_experience
            - top5_regions_by_experts
            - percent_high_rehire
            - avg_job_duration_all
            - avg_job_duration_by_category
            - avg_job_duration_by_region
            - avg_job_duration_by_experience
            - avg_job_duration_by_platform
            - avg_job_duration_by_project_type
            - avg_income_by_platform
            - avg_income_by_project_type

        Методы с параметром by (by: category, region, experience, platform, project_type):
            - avg_hourly_rate_by
            - avg_success_rate_by
            - avg_client_rating_by
            - avg_marketing_spend_by

        batch_analytics — универсальный инструмент для отчётов по нескольким метрикам.

        **Как вызывать batch_analytics:**
        Передавай список dict, где каждый dict:
            - {"method": "<имя_метода>"} — для методов без параметров
            - {"method": "<имя_метода>", "by": "<значение>"} — для методов с параметром by
    """

    system_prompt: str = f'{BASE_PROMPT}\n\n{METHODS_LIST}'


class Setting(BaseSettings):
    
    llm_groq: LLMGroqConfiguration = LLMGroqConfiguration()
    llm_gigachat: LLMGigaChatConfiguration = LLMGigaChatConfiguration()
    allowed_llm_model: str = 'llama3-70b-8192'
    # allowed_llm_model: str = 'GigaChat-2-max'
    csv_path: str = 'data/freelancer_earnings_bd.csv'

    first_message: str = 'Привет! Я ассистент, аналитик данных о фрилансерах. Чем могу помочь сегодня?'

    temperature: float = 0.1
    llm_response_color: str = '\033[35m'
    llm_response_color_reset: str = '\033[0m'

    max_length_human_prompt: int = 128
    max_history_pairs: int = 3
    max_batch_methods: int = 15 # максимальное количество инструментов (tools) за раз в batch_analytics
    

settings = Setting()
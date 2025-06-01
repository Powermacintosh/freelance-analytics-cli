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


class LLMGigaChatConfiguration(BaseModel):
    model: str = 'GigaChat-2-Max'
    verify_ssl_certs: bool = False
    api_key: str = os.getenv('GIGACHAT_API_KEY', '')


class Setting(BaseSettings):
    
    llm_groq: LLMGroqConfiguration = LLMGroqConfiguration()
    llm_gigachat: LLMGigaChatConfiguration = LLMGigaChatConfiguration()
    allowed_llm_model: str = 'llama3-70b-8192'
    # allowed_llm_model: str = 'GigaChat-2-Max'
    csv_path: str = 'data/freelancer_earnings_bd.csv'

    temperature: float = 0.1
    llm_response_color: str = '\033[35m'
    llm_response_color_reset: str = '\033[0m'

    max_retries_request_llm: int = 3 # количество попыток вызова при ошибке LLM
    sleep_time_for_retry_request_llm: int = 2 # время ожидания перед повторным вызовом при ошибке LLM
    
    BASE_PROMPT: str = (
        'Ты — ассистент, аналитик данных о фрилансерах.\n'
        'Твоя задача — понять какие данные пользователь хочет получить и вызвать соответствующую функцию.\n'
        'Если для ответа на вопрос пользователя требуется вызвать несколько инструментов (tools), то используй функцию batch_analytics.\n'
        'Вставляй результат вызова инструмента (tool) в ответ без изменений, без дополнительных комментариев, без перефразирования. И показывай пользователю.\n'
        'Всегда используй инструменты для аналитики, даже если кажется, что ты знаешь ответ.\n'
        'Не вызывай несуществующие инструменты.\n'
        'Отвечай только результатом, не указывай название инструмента или функцию, не добавляй префиксы.\n'
        'Не добавляй [tool_name]: в ответ.\n'
        'При ответе показывай результат с соблюдением переноса строк, пунктуации и форматирования.\n'
        'При получении результата из инструмента (tool) не надо отчитываться перед пользователем или его благодарить!\n'
        'И поскольку ты РУССКИЙ ассистент, веди диалог на РУССКОМ языке. Отвечай только на РУССКОМ языке.'
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

    BATCH_ANALYTICS_EXAMPLE: str = """
        **Пример для batch_analytics:**
        [
            {"method": "top5_regions_by_experts"},
            {"method": "avg_hourly_rate_by", "by": "platform"},
            {"method": "avg_hourly_rate_by", "by": "region"},
            {"method": "avg_hourly_rate_by", "by": "experience"},
            {"method": "avg_hourly_rate_by", "by": "project_type"},
            {"method": "avg_success_rate_by", "by": "region"},
            {"method": "percent_high_rehire"}
        ]

        Не добавляй параметр by к функциям, которые его не принимают (см. список выше).
    """
    system_prompt: str = f'{BASE_PROMPT}\n\n{METHODS_LIST}\n\n{BATCH_ANALYTICS_EXAMPLE}'

settings = Setting()
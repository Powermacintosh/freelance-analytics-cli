import uuid, sys, re, inspect, time,logging.config
from typing import Sequence, List, Dict, Any, Optional
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from core.schemas import BatchAnalyticsInput, BatchAnalyticsMethod
from core.data_analyzer import DataAnalyzer
from core.config import settings
from core.logger import logger_config

logging.config.dictConfig(logger_config)
logger = logging.getLogger('main_logger')
batch_analytics_logger = logging.getLogger('batch_analytics_logger')



class LLMAgent:
    def __init__(self, model: 'LanguageModelLike', tools: Sequence['BaseTool']) -> None:
        self._model = model
        self._agent = create_react_agent(
            model,
            tools=tools,
            checkpointer=InMemorySaver())
        self._config: RunnableConfig = {
            'configurable': {'thread_id': uuid.uuid4().hex}}

    def invoke(
        self,
        content: str,
        attachments: Optional[List[str]] = None,
        temperature: float = settings.temperature
    ) -> str:
        message: Dict[str, Any] = {
            'role': 'user',
            'content': content,
            **({'attachments': attachments} if attachments else {})
        }
        messages = [message]
        total_chars = 0
        for i, m in enumerate(messages):
            logger.info(remove_surrogates(f'Message[{i}]: {m}'))
            total_chars += sum(len(str(v)) for v in m.values() if isinstance(v, str))
        approx_tokens = total_chars // 4
        logger.info(remove_surrogates(f'Размер всех messages: {total_chars} символов, ~{approx_tokens} токенов'))
        logger.info(remove_surrogates(f'Thread_id: {self._config["configurable"]["thread_id"]}'))
        payload = {
            'messages': messages,
            'temperature': temperature,
            'max_tokens': 2048
        }
        logger.info(remove_surrogates(f'Параметры вызова LLM: {payload}'))
        try:
            result = self._agent.invoke(
                payload,
                config=self._config)
            return result['messages'][-1].content
        except Exception as e:
            logger.error(remove_surrogates(f'LLM ERROR: {e}'))
            if hasattr(e, 'status_code'):
                code = getattr(e, 'status_code')
                if code == 401:
                    return 'Ошибка LLM: неверный API-ключ или нет доступа (401 Unauthorized)'
                if code == 429:
                    return 'Ошибка LLM: превышен лимит запросов (429 Too Many Requests)'
                if code == 503:
                    return 'Ошибка LLM: сервис временно недоступен (503 Service Unavailable)'
                if code == 500:
                    return 'Ошибка LLM: внутренняя ошибка сервиса (500 Internal Server Error)'
                return f'Ошибка LLM: HTTP {code}'
            return f'Ошибка LLM: {e}'


def remove_surrogates(text: str) -> str:
    # Удаляет суррогатные пары (битые юникод-символы)
    return re.sub(r'[\ud800-\udfff]', '', text)


def print_agent_response(llm_response: str) -> None:
    cleaned = remove_surrogates(llm_response)
    print(f'{settings.llm_response_color}{cleaned}{settings.llm_response_color_reset}')


def get_user_prompt() -> str:
    return input('\nВы: ')


analyzer = DataAnalyzer()

@tool
def crypto_vs_other_income() -> str:
    """
    Насколько выше доход у фрилансеров, принимающих оплату в криптовалюте.
    """
    return analyzer.crypto_vs_other_income()

@tool
def income_by_region() -> str:
    """
    Как распределяется доход фрилансеров в зависимости от региона проживания?
    """
    return analyzer.income_by_region()

@tool
def percent_experts_lt_100_projects() -> str:
    """
    Какой процент фрилансеров, считающих себя экспертами, которые выполнили менее 100 проектов?
    """
    return analyzer.percent_experts_lt_100_projects()

@tool
def avg_income_by_category() -> str:
    """
    Средний доход по категориям работ.
    """
    return analyzer.avg_income_by_category()

@tool
def avg_income_by_experience() -> str:
    """
    Средний доход по уровню опыта.
    """
    return analyzer.avg_income_by_experience()

@tool
def top5_regions_by_experts() -> str:
    """
    Топ-5 регионов по количеству экспертов.
    """
    return analyzer.top5_regions_by_experts()

@tool
def percent_high_rehire() -> str:
    """
    Процент фрилансеров с повторным наймом выше 50%.
    """
    return analyzer.percent_high_rehire()

@tool
def avg_job_duration_all() -> str:
    """
    Среднее время выполнения работ по всем фрилансерам.
    """
    return analyzer.avg_job_duration_all()

@tool
def avg_job_duration_by_category() -> str:
    """
    Среднее время выполнения работ по категориям.
    """
    return analyzer.avg_job_duration_by_category()

@tool
def avg_job_duration_by_region() -> str:
    """
    Среднее время выполнения работ по регионам.
    """
    return analyzer.avg_job_duration_by_region()

@tool
def avg_job_duration_by_experience() -> str:
    """
    Среднее время выполнения работ по уровню опыта.
    """
    return analyzer.avg_job_duration_by_experience()

@tool
def avg_job_duration_by_platform() -> str:
    """
    Среднее время выполнения работ по платформам.
    """
    return analyzer.avg_job_duration_by_platform()

@tool
def avg_job_duration_by_project_type() -> str:
    """
    Среднее время выполнения работ по типу проекта.
    """
    return analyzer.avg_job_duration_by_project_type()

@tool
def avg_income_by_platform() -> str:
    """
    Средний доход по платформам.
    """
    return analyzer.avg_income_by_platform()

@tool
def avg_income_by_project_type() -> str:
    """
    Средний доход по типу проекта.
    """
    return analyzer.avg_income_by_project_type()

@tool
def avg_hourly_rate_by(by: str = 'category') -> str:
    """
    Средняя почасовая ставка по выбранному полю.
    """
    return analyzer.avg_hourly_rate_by(by)

@tool
def avg_success_rate_by(by: str = 'category') -> str:
    """
    Средний рейтинг завершенных проектов по выбранному полю.
    """
    return analyzer.avg_success_rate_by(by)

@tool
def avg_client_rating_by(by: str = 'category') -> str:
    """
    Средний рейтинг клиента по выбранному полю.
    """
    return analyzer.avg_client_rating_by(by)

@tool
def avg_marketing_spend_by(by: str = 'category') -> str:
    """
    Средние маркетинговые расходы, сгруппированные по одному из полей:
    - category (категория работы)
    - region (регион клиента)
    - experience (уровень опыта)
    - platform (платформа)
    - project_type (тип проекта)

    Параметр by определяет поле для группировки. По умолчанию — category.
    """
    return analyzer.avg_marketing_spend_by(by)

@tool(args_schema=BatchAnalyticsInput)
def batch_analytics(methods: List[BatchAnalyticsMethod]) -> str:
    """
    Универсальный инструмент для генерации отчёта по нескольким аналитическим вопросам.

    Каждый элемент списка methods — это dict с ключом:
      - method: имя метода
      - by: параметр группировки (для методов с by, опционально)

    Примеры:
    [
        {"method": "top5_regions_by_experts"},
        {"method": "avg_hourly_rate_by", "by": "platform"},
        {"method": "avg_success_rate_by", "by": "region"},
        {"method": "percent_high_rehire"}
    ]

    Если by не указан, используется значение по умолчанию (обычно category).
    """
    results = []
    for m in methods:
        method_name = m.method
        func = getattr(analyzer, method_name, None)
        batch_analytics_logger.info(f'batch_analytics: ищу метод {method_name} с параметрами {m.model_dump()}')
        if func:
            try:
                params = m.model_dump(exclude_unset=True)
                params.pop('method', None)
                sig = inspect.signature(func)
                filtered_params = {k: v for k, v in params.items() if k in sig.parameters}
                batch_analytics_logger.info(f'batch_analytics: вызываю {method_name} с параметрами {filtered_params}')
                result = func(**filtered_params)
                batch_analytics_logger.info(f'batch_analytics: результат {method_name}: {result}')
                results.append(f'{result}')
            except Exception as e:
                batch_analytics_logger.error(f'batch_analytics: ошибка при вызове {method_name} с параметрами {params}: {e}')
                results.append(f'Извините, отвлёкся) повторите вопрос.')
        else:
            batch_analytics_logger.warning(f'batch_analytics: метод {method_name} не найден')
            results.append(f'Извините, отвлёкся, повторите ваш вопрос.')
    return '\n\n'.join(results)


def main() -> None:
    try:
        if settings.llm_groq.model == settings.allowed_llm_model:
            model = ChatOpenAI(
                model=settings.llm_groq.model,
                base_url=settings.llm_groq.base_url,
                api_key=settings.llm_groq.api_key
            )
        elif settings.llm_gigachat.model == settings.allowed_llm_model:
            model = GigaChat(
                credentials=settings.llm_gigachat.api_key,
                model=settings.llm_gigachat.model,
                verify_ssl_certs=settings.llm_gigachat.verify_ssl_certs
            )
        else:
            raise ValueError(f'Модель {settings.llm_groq.model} или {settings.llm_gigachat.model} не поддерживается')

        agent = LLMAgent(model, tools=[
            crypto_vs_other_income,
            income_by_region,
            percent_experts_lt_100_projects,
            avg_income_by_category,
            avg_income_by_experience,
            top5_regions_by_experts,
            percent_high_rehire,
            avg_job_duration_all,
            avg_job_duration_by_category,
            avg_job_duration_by_region,
            avg_job_duration_by_experience,
            avg_job_duration_by_platform,
            avg_job_duration_by_project_type,
            avg_income_by_platform,
            avg_income_by_project_type,
            avg_marketing_spend_by,
            avg_hourly_rate_by,
            avg_success_rate_by,
            avg_client_rating_by,
            batch_analytics
        ])
        agent_response = agent.invoke(content=settings.system_prompt)

        while True:
            # retry logic
            max_retries = settings.max_retries_request_llm
            retries = 0
            response = agent_response
            while response.strip().startswith('Ошибка LLM') and retries < max_retries:
                time.sleep(settings.sleep_time_for_retry_request_llm * (2 ** retries))
                response = agent.invoke('?')
                retries += 1
            print_agent_response(response)

            # print_agent_response(agent_response)
            agent_response = agent.invoke(get_user_prompt())
    except Exception as e:
        logger.error(remove_surrogates(f'CRITICAL ERROR: {e}'))
        sys.exit(1)


if __name__ == '__main__':
    main()

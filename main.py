import uuid, sys, re, inspect, logging.config
from typing import Sequence, List, Union
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from core.schemas import (
    AvgHourlyRateByInput,
    AvgSuccessRateByInput,
    AvgClientRatingByInput,
    AvgMarketingSpendByInput,
    BatchAnalyticsInput,
    BatchAnalyticsMethod,
)
from core.data_analyzer import DataAnalyzer
from core.config import settings
from core.logger import logger_config
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage


logging.config.dictConfig(logger_config)
logger = logging.getLogger('main_logger')
batch_analytics_logger = logging.getLogger('batch_analytics_logger')
trim_logger = logging.getLogger('trim_logger')
deduped_logger = logging.getLogger('deduped_logger')


class LLMAgent:

    def __init__(self, model: 'LanguageModelLike', system_prompt: str, tools: Sequence['BaseTool']) -> None:
        self._model = model
        self._system_prompt = system_prompt
        self._config: RunnableConfig = {
            'configurable': {'thread_id': uuid.uuid4().hex}}
        self._agent = create_react_agent(
            model,
            tools=tools,
            checkpointer=InMemorySaver(),
            pre_model_hook=self._pre_model_hook
        )

    def _deduplicate_messages(
        self,
        messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolMessage]],
        deduped: bool = False
    ) -> List[Union[SystemMessage, HumanMessage, AIMessage, ToolMessage]]:
        """Удаляет дублирующиеся пары сообщений, сохраняя только уникальные пары."""
        deduped_logger.info('=== DEDUPLICATION START ===')
        deduped_logger.info(f'Всего сообщений на входе: {len(messages)}')
        
        # Сохраняем системное сообщение
        system_msg = next((m for m in messages if isinstance(m, SystemMessage)), None)
        
        # Группируем сообщения в пары
        pairs = []
        current_pair = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue
                
            current_pair.append(msg)
            
            # Если это ToolMessage или последнее сообщение, завершаем пару
            if isinstance(msg, ToolMessage) or msg == messages[-1]:
                if current_pair:
                    pairs.append(current_pair)
                    current_pair = []
        
        # Считаем дубликаты пар
        pair_counts = {}
        pair_details = {}
        
        for pair in pairs:
            # Создаем ключ пары из контента всех сообщений
            pair_key = tuple(msg.content for msg in pair)
            
            if pair_key not in pair_counts:
                pair_counts[pair_key] = 0
                pair_details[pair_key] = []
            pair_counts[pair_key] += 1
            pair_details[pair_key].append([{
                'type': type(msg).__name__,
                'id': getattr(msg, 'id', 'no_id'),
                'name': getattr(msg, 'name', 'no_name')
            } for msg in pair])
            
        # Логируем дубликаты пар
        for pair_key, count in pair_counts.items():
            if count > 1:
                deduped_logger.info(f'Найдена дублирующаяся пара! Встречается {count} раз:')
                for pair_detail in pair_details[pair_key]:
                    deduped_logger.info('  Пара:')
                    for msg_detail in pair_detail:
                        deduped_logger.info(f'    - {msg_detail["type"]} (id: {msg_detail["id"]}, name: {msg_detail["name"]})')
                
        if not deduped:
            deduped_logger.info('=== DEDUPLICATION END (только подсчет) ===')
            return messages
                
        # Удаляем дубликаты пар, сохраняя порядок
        seen_pairs = set()
        deduped_messages = []
        
        if system_msg:
            deduped_messages.append(system_msg)
            
        for pair in pairs:
            pair_key = tuple(msg.content for msg in pair)
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                deduped_messages.extend(pair)
                deduped_logger.info(f'Сохраняю уникальную пару: {[type(msg).__name__ for msg in pair]}')
                
        deduped_logger.info('=== DEDUPLICATION END (удаление дубликатов) ===')
        deduped_logger.info(f'Было сообщений: {len(messages)}, стало: {len(deduped_messages)}')
        return deduped_messages

    def _trim_messages_by_pairs(
        self,
        messages: List[Union[SystemMessage, HumanMessage, AIMessage, ToolMessage]],
        max_pairs: int
    ) -> List[Union[SystemMessage, HumanMessage, AIMessage, ToolMessage]]:
        trim_logger.info('=== TRIMMING START ===')
        
        # Сохраняем системное сообщение
        sys = [m for m in messages if isinstance(m, SystemMessage)]
        if sys:
            trim_logger.info(f'Найдено системное сообщение: {sys[0].content[:50]}...')
        
        # Группируем сообщения в пары
        pairs = []
        current_pair = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue
                
            if isinstance(msg, HumanMessage):
                if current_pair:  # Если есть предыдущая пара
                    pairs.append(current_pair)
                current_pair = [msg]  # Начинаем новую пару
            elif current_pair:  # Добавляем к текущей паре
                current_pair.append(msg)
                
        if current_pair:  # Добавляем последнюю пару
            pairs.append(current_pair)
        
        trim_logger.info('=== TRIMMING UPDATE ===')
        # Берем последние max_pairs пар
        trimmed_pairs = pairs[-max_pairs:] if len(pairs) > max_pairs else pairs
        trim_logger.info(f'Найдено пар: {len(pairs)}, будет сохранено пар: {len(trimmed_pairs)}')
        
        # Формируем финальный список
        result = []
        if sys:
            result.append(sys[0])
            
        for pair in trimmed_pairs:
            result.extend(pair)
            
        trim_logger.info(f'Было сообщений: {len(messages)}, стало: {len(result)}')
        trim_logger.info('Финальный стек:')
        for idx, msg in enumerate(result):
            trim_logger.info(f'[{idx}] {type(msg).__name__}: {msg.content[:50]}...')
        trim_logger.info('=== TRIMMING END ===')
        return result

    def _pre_model_hook(self, state):
        state['messages'] = self._deduplicate_messages(state['messages'])
        trimmed = self._trim_messages_by_pairs(
            state['messages'],
            settings.max_history_pairs
        )
        return {'llm_input_messages': trimmed}

    def _check_user_prompt_length(self, message: HumanMessage, max_tokens: int) -> None:
        tokens = count_tokens_approximately([message])
        if tokens > max_tokens:
            logger.error(f'User prompt слишком длинный: {tokens} токенов (лимит {max_tokens})')
            raise ValueError(f'Слишком длинный запрос, попробуйте его сократить')

    def invoke(
        self,
        content: str,
        temperature: float = settings.temperature
    ) -> str:
        logger.info(remove_surrogates(f'Thread_id: {self._config["configurable"]["thread_id"]}'))
        # Добавляем system prompt при первом запросе
        try:
            state = self._agent.get_state(self._config)
            messages = state.values.get('messages', [])
        except Exception:
            messages = []
        user_message = HumanMessage(content=content)
        self._check_user_prompt_length(user_message, settings.max_human_tokens)
        if not messages:
            payload_messages = [
                {'role': 'system', 'content': self._system_prompt},
                {'role': 'user', 'content': content}
            ]
        else:
            payload_messages = [{'role': 'user', 'content': content}]
        payload = {
            'messages': payload_messages,
            'temperature': temperature,
        }
        logger.info(remove_surrogates(f'Параметры вызова LLM: {payload}'))
        try:
            result = self._agent.invoke(
                payload,
                config=self._config)
            llm_response = result['messages'][-1].content
            usage = None
            if isinstance(result, dict) and 'messages' in result:
                for msg in reversed(result['messages']):
                    if hasattr(msg, 'response_metadata') and msg.response_metadata and 'token_usage' in msg.response_metadata:
                        usage = msg.response_metadata['token_usage']
                        break
            if usage:
                logger.info(f"Токены и расходы: {usage}")
            return llm_response
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



@tool('crypto_vs_other_income', return_direct=True)
def crypto_vs_other_income() -> str:
    """Насколько выше доход у фрилансеров, принимающих оплату в криптовалюте."""
    return analyzer.crypto_vs_other_income()

@tool('income_by_region', return_direct=True)
def income_by_region() -> str:
    """Как распределяется доход фрилансеров в зависимости от региона проживания?"""
    return analyzer.income_by_region()

@tool('percent_experts_lt_100_projects', return_direct=True)
def percent_experts_lt_100_projects() -> str:
    """Какой процент фрилансеров, считающих себя экспертами, которые выполнили менее 100 проектов?"""
    return analyzer.percent_experts_lt_100_projects()

@tool('avg_income_by_category', return_direct=True)
def avg_income_by_category() -> str:
    """Средний доход по категориям работ."""
    return analyzer.avg_income_by_category()

@tool('avg_income_by_experience', return_direct=True)
def avg_income_by_experience() -> str:
    """Средний доход по уровню опыта."""
    return analyzer.avg_income_by_experience()

@tool('top5_regions_by_experts', return_direct=True)
def top5_regions_by_experts() -> str:
    """Топ-5 регионов по количеству экспертов."""
    return analyzer.top5_regions_by_experts()

@tool('percent_high_rehire', return_direct=True)
def percent_high_rehire() -> str:
    """Процент фрилансеров с повторным наймом выше 50%."""
    return analyzer.percent_high_rehire()

@tool('avg_job_duration_all', return_direct=True)
def avg_job_duration_all() -> str:
    """Среднее время выполнения работ по всем фрилансерам."""
    return analyzer.avg_job_duration_all()

@tool('avg_job_duration_by_category', return_direct=True)
def avg_job_duration_by_category() -> str:
    """Среднее время выполнения работ по категориям."""
    return analyzer.avg_job_duration_by_category()

@tool('avg_job_duration_by_region', return_direct=True)
def avg_job_duration_by_region() -> str:
    """Среднее время выполнения работ по регионам."""
    return analyzer.avg_job_duration_by_region()

@tool('avg_job_duration_by_experience', return_direct=True)
def avg_job_duration_by_experience() -> str:
    """Среднее время выполнения работ по уровню опыта."""
    return analyzer.avg_job_duration_by_experience()

@tool('avg_job_duration_by_platform', return_direct=True)
def avg_job_duration_by_platform() -> str:
    """Среднее время выполнения работ по платформам."""
    return analyzer.avg_job_duration_by_platform()

@tool('avg_job_duration_by_project_type', return_direct=True)
def avg_job_duration_by_project_type() -> str:
    """Среднее время выполнения работ по типу проекта."""
    return analyzer.avg_job_duration_by_project_type()

@tool('avg_income_by_platform', return_direct=True)
def avg_income_by_platform() -> str:
    """Средний доход по платформам."""
    return analyzer.avg_income_by_platform()

@tool('avg_income_by_project_type', return_direct=True)
def avg_income_by_project_type() -> str:
    """Средний доход по типу проекта."""
    return analyzer.avg_income_by_project_type()

@tool('avg_hourly_rate_by', args_schema=AvgHourlyRateByInput, return_direct=True)
def avg_hourly_rate_by(by: str = 'category') -> str:
    """Средняя почасовая ставка по выбранному полю."""
    return analyzer.avg_hourly_rate_by(by)

@tool('avg_success_rate_by', args_schema=AvgSuccessRateByInput, return_direct=True)
def avg_success_rate_by(by: str = 'category') -> str:
    """Средний рейтинг завершенных проектов по выбранному полю."""
    return analyzer.avg_success_rate_by(by)

@tool('avg_client_rating_by', args_schema=AvgClientRatingByInput, return_direct=True)
def avg_client_rating_by(by: str = 'category') -> str:
    """Средний рейтинг клиента по выбранному полю."""
    return analyzer.avg_client_rating_by(by)

@tool('avg_marketing_spend_by', args_schema=AvgMarketingSpendByInput, return_direct=True)
def avg_marketing_spend_by(by: str = 'category') -> str:
    """Средние маркетинговые расходы, сгруппированные по одному из полей."""
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
    batch_analytics_logger.warning(f'batch_analytics: вызвано методов: {len(methods)}')
    if len(methods) > settings.max_batch_methods:
        methods = methods[:settings.max_batch_methods]
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
                batch_analytics_logger.info(f'batch_analytics: результат {method_name}')
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
            system_prompt = settings.llm_groq.system_prompt
            model = ChatOpenAI(
                model=settings.llm_groq.model,
                base_url=settings.llm_groq.base_url,
                api_key=settings.llm_groq.api_key
            )
        elif settings.llm_gigachat.model == settings.allowed_llm_model:
            system_prompt = settings.llm_gigachat.system_prompt
            model = GigaChat(
                credentials=settings.llm_gigachat.api_key,
                model=settings.llm_gigachat.model,
                verify_ssl_certs=settings.llm_gigachat.verify_ssl_certs
            )
        else:
            raise ValueError(f'Модель {settings.llm_groq.model} или {settings.llm_gigachat.model} не поддерживается')

        agent = LLMAgent(model, system_prompt, tools=[
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
        agent_response = None
        print_agent_response(settings.first_message)
        while True:
            if agent_response is not None:
                print_agent_response(agent_response)
            prompt = get_user_prompt()
            try:
                agent_response = agent.invoke(prompt)
            except ValueError as e:
                print(f'{settings.llm_response_color}{e}{settings.llm_response_color_reset}')
    except Exception as e:
        logger.error(remove_surrogates(f'CRITICAL ERROR: {e}'))
        sys.exit(1)


if __name__ == '__main__':
    main()

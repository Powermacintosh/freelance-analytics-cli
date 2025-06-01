from typing import List, Dict, Any
from core.config import settings
import csv, time, functools,logging.config
from core.logger import logger_config

logging.config.dictConfig(logger_config)
logger = logging.getLogger('data_analyzer_logger')

class DataAnalyzer:
    """Класс для аналитики данных о фрилансерах."""
    def __init__(self, path: str = settings.csv_path):
        self.data: List[Dict[str, Any]] = self._load_csv(path)

    def _load_csv(self, path: str) -> List[Dict[str, Any]]:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [self._convert_types(row) for row in reader]
    
    def _safe_duration(self, val):
        try:
            return float(val)
        except Exception:
            return None

    def _convert_types(self, row: Dict[str, str]) -> Dict[str, Any]:
        # Приводим нужные поля к числам
        for key in ['Earnings_USD', 'Job_Completed', 'Rehire_Rate', 'Marketing_Spend']:
            try:
                row[key] = float(row[key]) if '.' in row[key] else int(row[key])
            except Exception:
                row[key] = 0
        return row

    @staticmethod
    def log_time(func):
        def wrapper(self, *args, **kwargs):
            start = time.time()
            result = func(self, *args, **kwargs)
            elapsed = time.time() - start
            logger.info(f'{func.__name__} выполнен за {elapsed:.3f} сек')
            return result
        return functools.wraps(func)(wrapper)

    @log_time
    def crypto_vs_other_income(self) -> str:
        crypto = [r.get('Earnings_USD', 0) for r in self.data if r.get('Payment_Method') == 'Crypto']
        other = [r.get('Earnings_USD', 0) for r in self.data if r.get('Payment_Method') != 'Crypto']
        if not crypto or not other:
            return 'Недостаточно данных для анализа.'
        avg_crypto = sum(crypto) / len(crypto)
        avg_other = sum(other) / len(other)
        diff = avg_crypto - avg_other
        percent = (diff / avg_other) * 100
        return (
            f'Средний доход фрилансеров с оплатой в криптовалюте: {avg_crypto:.2f} USD.\n'
            f'Средний доход с другими способами: {avg_other:.2f} USD.\n'
            f'Разница: {diff:.2f} USD ({percent:.1f}%)'
        )

    @log_time
    def income_by_region(self) -> str:
        region_sums: Dict[str, float] = {}
        region_counts: Dict[str, int] = {}
        for r in self.data:
            region = r.get('Client_Region', 'Unknown')
            region_sums[region] = region_sums.get(region, 0.0) + r.get('Earnings_USD', 0)
            region_counts[region] = region_counts.get(region, 0) + 1
        if not region_sums:
            return 'Недостаточно данных для анализа.'
        region_avg = {region: region_sums[region] / region_counts[region] for region in region_sums}
        sorted_regions = sorted(region_avg.items(), key=lambda x: x[1], reverse=True)
        result = 'Средний доход по регионам:\n'
        for region, income in sorted_regions:
            result += f'- {region}: {income:.2f} USD\n'
        return result

    @log_time
    def percent_experts_lt_100_projects(self) -> str:
        experts = [r for r in self.data if r.get('Experience_Level') == 'Expert']
        if not experts:
            return 'Нет данных по экспертам.'
        lt_100 = [r for r in experts if r.get('Job_Completed', 0) < 100]
        percent = (len(lt_100) / len(experts)) * 100
        return f"{percent:.1f}% экспертов выполнили менее 100 проектов ({len(lt_100)}/{len(experts)})."

    @log_time
    def avg_income_by_category(self) -> str:
        categories: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for r in self.data:
            cat = r.get('Job_Category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + r.get('Earnings_USD', 0)
            counts[cat] = counts.get(cat, 0) + 1
        if not categories:
            return 'Недостаточно данных для анализа.'
        result = 'Средний доход по категориям работ:\n'
        for cat in categories:
            avg = categories[cat] / counts[cat]
            result += f'- {cat}: {avg:.2f} USD\n'
        return result

    @log_time
    def avg_income_by_experience(self) -> str:
        levels: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for r in self.data:
            lvl = r.get('Experience_Level', 'Unknown')
            levels[lvl] = levels.get(lvl, 0) + r.get('Earnings_USD', 0)
            counts[lvl] = counts.get(lvl, 0) + 1
        if not levels:
            return 'Недостаточно данных для анализа.'
        result = 'Средний доход по уровню опыта:\n'
        for lvl in levels:
            avg = levels[lvl] / counts[lvl]
            result += f'- {lvl}: {avg:.2f} USD\n'
        return result

    @log_time
    def top5_regions_by_experts(self) -> str:
        region_experts: Dict[str, int] = {}
        for r in self.data:
            if r.get('Experience_Level') == 'Expert':
                region = r.get('Client_Region', 'Unknown')
                region_experts[region] = region_experts.get(region, 0) + 1
        if not region_experts:
            return 'Нет данных по регионам.'
        sorted_regions = sorted(region_experts.items(), key=lambda x: x[1], reverse=True)[:5]
        result = 'Топ-5 регионов по количеству экспертов:\n'
        for region, count in sorted_regions:
            result += f'- {region}: {count}\n'
        return result

    @log_time
    def percent_high_rehire(self, threshold: float = 50.0) -> str:
        high_rehire = [r for r in self.data if r.get('Rehire_Rate', 0) > threshold]
        percent = (len(high_rehire) / len(self.data)) * 100 if self.data else 0
        return f'Процент фрилансеров с повторным наймом выше {threshold}%: {percent:.1f}% ({len(high_rehire)}/{len(self.data)})'

    @log_time
    def avg_job_duration_all(self) -> str:
        durations = [self._safe_duration(r.get('Job_Duration_Days', 0)) for r in self.data]
        durations = [d for d in durations if d and d > 0]
        if not durations:
            return 'Нет данных о длительности выполнения работ.'
        avg = sum(durations) / len(durations)
        return f'Среднее время выполнения работ: {avg:.1f} дней'

    @log_time
    def avg_job_duration_by_category(self) -> str:
        sum_map, count_map = {}, {}
        for r in self.data:
            k = r.get('Job_Category', 'Unknown')
            dur = self._safe_duration(r.get('Job_Duration_Days', 0))
            if dur and dur > 0:
                sum_map[k] = sum_map.get(k, 0) + dur
                count_map[k] = count_map.get(k, 0) + 1
        if not sum_map:
            return 'Нет данных по категориям.'
        res = ['Среднее время выполнения по категориям:']
        for k in sum_map:
            res.append(f'- {k}: {sum_map[k]/count_map[k]:.1f} дней')
        return '\n'.join(res)

    @log_time
    def avg_job_duration_by_region(self) -> str:
        sum_map, count_map = {}, {}
        for r in self.data:
            k = r.get('Client_Region', 'Unknown')
            dur = self._safe_duration(r.get('Job_Duration_Days', 0))
            if dur and dur > 0:
                sum_map[k] = sum_map.get(k, 0) + dur
                count_map[k] = count_map.get(k, 0) + 1
        if not sum_map:
            return 'Нет данных по регионам.'
        res = ['Среднее время выполнения по регионам:']
        for k in sum_map:
            res.append(f'- {k}: {sum_map[k]/count_map[k]:.1f} дней')
        return '\n'.join(res)

    @log_time
    def avg_job_duration_by_experience(self) -> str:
        sum_map, count_map = {}, {}
        for r in self.data:
            k = r.get('Experience_Level', 'Unknown')
            dur = self._safe_duration(r.get('Job_Duration_Days', 0))
            if dur and dur > 0:
                sum_map[k] = sum_map.get(k, 0) + dur
                count_map[k] = count_map.get(k, 0) + 1
        if not sum_map:
            return 'Нет данных по уровню опыта.'
        res = ['Среднее время выполнения по уровню опыта:']
        for k in sum_map:
            res.append(f'- {k}: {sum_map[k]/count_map[k]:.1f} дней')
        return '\n'.join(res)

    @log_time
    def avg_job_duration_by_platform(self) -> str:
        sum_map, count_map = {}, {}
        for r in self.data:
            k = r.get('Platform', 'Unknown')
            dur = self._safe_duration(r.get('Job_Duration_Days', 0))
            if dur and dur > 0:
                sum_map[k] = sum_map.get(k, 0) + dur
                count_map[k] = count_map.get(k, 0) + 1
        if not sum_map:
            return 'Нет данных по платформам.'
        res = ['Среднее время выполнения по платформам:']
        for k in sum_map:
            res.append(f'- {k}: {sum_map[k]/count_map[k]:.1f} дней')
        return '\n'.join(res)

    @log_time
    def avg_job_duration_by_project_type(self) -> str:
        sum_map, count_map = {}, {}
        for r in self.data:
            k = r.get('Project_Type', 'Unknown')
            dur = self._safe_duration(r.get('Job_Duration_Days', 0))
            if dur and dur > 0:
                sum_map[k] = sum_map.get(k, 0) + dur
                count_map[k] = count_map.get(k, 0) + 1
        if not sum_map:
            return 'Нет данных по типу проекта.'
        res = ['Среднее время выполнения по типу проекта:']
        for k in sum_map:
            res.append(f'- {k}: {sum_map[k]/count_map[k]:.1f} дней')
        return '\n'.join(res)

    @log_time
    def avg_income_by_platform(self) -> str:
        sums, counts = {}, {}
        for r in self.data:
            plat = r.get('Platform', 'Unknown')
            sums[plat] = sums.get(plat, 0) + r.get('Earnings_USD', 0)
            counts[plat] = counts.get(plat, 0) + 1
        if not sums:
            return 'Нет данных по платформам.'
        res = 'Средний доход по платформам:\n'
        for plat in sums:
            res += f'- {plat}: {sums[plat]/counts[plat]:.2f} USD\n'
        return res
    
    @log_time
    def avg_income_by_project_type(self) -> str:
        sums, counts = {}, {}
        for r in self.data:
            t = r.get('Project_Type', 'Unknown')
            sums[t] = sums.get(t, 0) + r.get('Earnings_USD', 0)
            counts[t] = counts.get(t, 0) + 1
        if not sums:
            return 'Нет данных по типу проекта.'
        res = 'Средний доход по типу проекта:\n'
        for t in sums:
            res += f'- {t}: {sums[t]/counts[t]:.2f} USD\n'
        return res

    @log_time
    def avg_hourly_rate_by(self, by: str = 'category') -> str:
        key_map = {
            'category': 'Job_Category',
            'region': 'Client_Region',
            'experience': 'Experience_Level',
            'platform': 'Platform',
            'project_type': 'Project_Type'
        }
        key = key_map.get(by, 'Job_Category')
        sums, counts = {}, {}
        for r in self.data:
            k = r.get(key, 'Unknown')
            rate = r.get('Hourly_Rate', None)
            if rate is not None:
                try:
                    rate = float(rate)
                except Exception:
                    continue
                sums[k] = sums.get(k, 0) + rate
                counts[k] = counts.get(k, 0) + 1
        if not sums:
            return f'Нет данных по {by}.'
        res = f'Средняя ставка (Hourly Rate) по {by}:\n'
        for k in sums:
            res += f'- {k}: {sums[k]/counts[k]:.2f} USD/ч\n'
        return res

    @log_time
    def avg_success_rate_by(self, by: str = 'category') -> str:
        key_map = {
            'category': 'Job_Category',
            'region': 'Client_Region',
            'experience': 'Experience_Level',
            'platform': 'Platform',
            'project_type': 'Project_Type'
        }
        key = key_map.get(by, 'Job_Category')
        sums, counts = {}, {}
        for r in self.data:
            k = r.get(key, 'Unknown')
            rate = r.get('Job_Success_Rate', None)
            if rate is not None:
                try:
                    rate = float(rate)
                except Exception:
                    continue
                sums[k] = sums.get(k, 0) + rate
                counts[k] = counts.get(k, 0) + 1
        if not sums:
            return f'Нет данных по {by}.'
        res = f'Средний Job Success Rate по {by}:\n'
        for k in sums:
            res += f'- {k}: {sums[k]/counts[k]:.1f}%\n'
        return res

    @log_time
    def avg_client_rating_by(self, by: str = 'category') -> str:
        key_map = {
            'category': 'Job_Category',
            'region': 'Client_Region',
            'experience': 'Experience_Level',
            'platform': 'Platform',
            'project_type': 'Project_Type'
        }
        key = key_map.get(by, 'Job_Category')
        sums, counts = {}, {}
        for r in self.data:
            k = r.get(key, 'Unknown')
            rating = r.get('Client_Rating', None)
            if rating is not None:
                try:
                    rating = float(rating)
                except Exception:
                    continue
                sums[k] = sums.get(k, 0) + rating
                counts[k] = counts.get(k, 0) + 1
        if not sums:
            return f'Нет данных по {by}.'
        res = f'Средний рейтинг клиента по {by}:\n'
        for k in sums:
            res += f'- {k}: {sums[k]/counts[k]:.2f}\n'
        return res

    @log_time
    def avg_marketing_spend_by(self, by: str = 'category') -> str:
        key_map = {
            'category': 'Job_Category',
            'region': 'Client_Region',
            'experience': 'Experience_Level',
            'platform': 'Platform',
            'project_type': 'Project_Type'
        }
        key = key_map.get(by, 'Job_Category')
        sums, counts = {}, {}
        for r in self.data:
            k = r.get(key, 'Unknown')
            spend = r.get('Marketing_Spend', None)
            if spend is not None:
                try:
                    spend = float(spend)
                except Exception:
                    continue
                sums[k] = sums.get(k, 0) + spend
                counts[k] = counts.get(k, 0) + 1
        if not sums:
            return f'Нет данных по {by}.'
        res = f'Средние маркетинговые расходы по {by}:\n'
        for k in sums:
            res += f'- {k}: {sums[k]/counts[k]:.2f} USD\n'
        return res
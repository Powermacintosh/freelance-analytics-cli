import pytest
from core.data_analyzer import DataAnalyzer

# Edge-case datasets
EMPTY_DATA = []
ALL_CRYPTO = [{
    'Earnings_USD': 100,
    'Payment_Method': 'Crypto',
    'Client_Region': 'RU',
    'Experience_Level': 'Expert',
    'Job_Completed': 10,
    'Job_Category': 'Design',
    'Rehire_Rate': 60,
    'Job_Duration_Days': 5
} for _ in range(3)]
NO_EXPERTS = [{
    'Earnings_USD': 200,
    'Payment_Method': 'Card',
    'Client_Region': 'US',
    'Experience_Level': 'Beginner',
    'Job_Completed': 5,
    'Job_Category': 'Programming',
    'Rehire_Rate': 10,
    'Job_Duration_Days': 0
} for _ in range(2)]
NEGATIVE_ZERO = [
    {'Earnings_USD': 0, 'Payment_Method': 'Card', 'Client_Region': 'IN', 'Experience_Level': 'Expert', 'Job_Completed': 0, 'Job_Category': 'Design', 'Rehire_Rate': -10, 'Job_Duration_Days': 0},
    {'Earnings_USD': -100, 'Payment_Method': 'Crypto', 'Client_Region': 'RU', 'Experience_Level': 'Expert', 'Job_Completed': 0, 'Job_Category': 'Programming', 'Rehire_Rate': 0, 'Job_Duration_Days': -5}
]
MISSING_FIELDS = [
    {'Earnings_USD': 100, 'Payment_Method': 'Card'},
    {'Earnings_USD': 200, 'Payment_Method': 'Crypto'}
]

class EdgeAnalyzer(DataAnalyzer):
    def __init__(self, data):
        self.data = data

@pytest.mark.parametrize('data,expect', [
    (EMPTY_DATA, 'Недостаточно данных'),
    (ALL_CRYPTO, 'Недостаточно данных'),
])
def test_crypto_vs_other_income_edge(data, expect):
    out = EdgeAnalyzer(data).crypto_vs_other_income()
    assert expect in out

def test_percent_experts_lt_100_projects_no_experts():
    out = EdgeAnalyzer(NO_EXPERTS).percent_experts_lt_100_projects()
    assert 'Нет данных' in out

def test_crypto_vs_other_income_empty():
    out = EdgeAnalyzer(EMPTY_DATA).crypto_vs_other_income()
    assert 'Недостаточно данных' in out

def test_income_by_region_missing_fields():
    out = EdgeAnalyzer(MISSING_FIELDS).income_by_region()
    assert 'Unknown' in out

def test_percent_experts_lt_100_projects_empty():
    out = EdgeAnalyzer(EMPTY_DATA).percent_experts_lt_100_projects()
    assert 'Нет данных' in out

def test_avg_job_duration_all_negative_zero():
    out = EdgeAnalyzer(NEGATIVE_ZERO).avg_job_duration_all()
    assert 'Нет данных' in out or '0.0' not in out

def test_avg_income_by_category_missing():
    out = EdgeAnalyzer(MISSING_FIELDS).avg_income_by_category()
    assert 'Unknown' in out or 'Недостаточно данных' in out

def test_avg_income_by_platform_missing():
    out = EdgeAnalyzer(MISSING_FIELDS).avg_income_by_platform()
    assert 'Unknown' in out or 'Нет данных' in out

def test_missing_fields():
    a = EdgeAnalyzer(MISSING_FIELDS)
    # Ожидаем, что в выводе будет 'Unknown', а не KeyError
    assert 'Unknown' in a.income_by_region() 
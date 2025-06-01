import pytest
from core.data_analyzer import DataAnalyzer

class DummySettings:
    csv_path = None

TEST_DATA = [
    {
        'Earnings_USD': 1000,
        'Payment_Method': 'Crypto',
        'Client_Region': 'RU',
        'Experience_Level': 'Expert',
        'Job_Completed': 120,
        'Job_Category': 'Design',
        'Rehire_Rate': 60,
        'Job_Duration_Days': 10,
        'Platform': 'Upwork',
        'Project_Type': 'Web',
        'Hourly_Rate': 50,
        'Job_Success_Rate': 98,
        'Client_Rating': 4.9,
        'Marketing_Spend': 100
    },
    {
        'Earnings_USD': 800,
        'Payment_Method': 'Card',
        'Client_Region': 'US',
        'Experience_Level': 'Intermediate',
        'Job_Completed': 80,
        'Job_Category': 'Programming',
        'Rehire_Rate': 30,
        'Job_Duration_Days': 20,
        'Platform': 'Freelancer',
        'Project_Type': 'Mobile',
        'Hourly_Rate': 40,
        'Job_Success_Rate': 90,
        'Client_Rating': 4.5,
        'Marketing_Spend': 50
    },
    {
        'Earnings_USD': 1200,
        'Payment_Method': 'Crypto',
        'Client_Region': 'RU',
        'Experience_Level': 'Expert',
        'Job_Completed': 200,
        'Job_Category': 'Programming',
        'Rehire_Rate': 80,
        'Job_Duration_Days': 5,
        'Platform': 'Upwork',
        'Project_Type': 'Web',
        'Hourly_Rate': 60,
        'Job_Success_Rate': 99,
        'Client_Rating': 5.0,
        'Marketing_Spend': 200
    },
    {
        'Earnings_USD': 500,
        'Payment_Method': 'Card',
        'Client_Region': 'IN',
        'Experience_Level': 'Beginner',
        'Job_Completed': 30,
        'Job_Category': 'Design',
        'Rehire_Rate': 10,
        'Job_Duration_Days': 15,
        'Platform': 'Freelancer',
        'Project_Type': 'Mobile',
        'Hourly_Rate': 20,
        'Job_Success_Rate': 85,
        'Client_Rating': 4.0,
        'Marketing_Spend': 0
    }
]

class DataAnalyzerForTest(DataAnalyzer):
    def __init__(self):
        self.data = TEST_DATA

@pytest.fixture
def analyzer():
    return DataAnalyzerForTest()

def test_crypto_vs_other_income(analyzer):
    out = analyzer.crypto_vs_other_income()
    assert 'криптовалюте' in out and 'USD' in out

def test_income_by_region(analyzer):
    out = analyzer.income_by_region()
    assert 'RU' in out and 'US' in out and 'IN' in out

def test_percent_experts_lt_100_projects(analyzer):
    out = analyzer.percent_experts_lt_100_projects()
    assert '%' in out

def test_avg_income_by_category(analyzer):
    out = analyzer.avg_income_by_category()
    assert 'Design' in out and 'Programming' in out

def test_avg_income_by_experience(analyzer):
    out = analyzer.avg_income_by_experience()
    assert 'Expert' in out and 'Intermediate' in out and 'Beginner' in out

def test_top5_regions_by_experts(analyzer):
    out = analyzer.top5_regions_by_experts()
    assert 'RU' in out

def test_percent_high_rehire(analyzer):
    out = analyzer.percent_high_rehire()
    assert '%' in out

def test_avg_job_duration_all(analyzer):
    out = analyzer.avg_job_duration_all()
    assert 'дней' in out

def test_avg_job_duration_by_category(analyzer):
    out = analyzer.avg_job_duration_by_category()
    assert 'Design' in out and 'Programming' in out

def test_avg_job_duration_by_region(analyzer):
    out = analyzer.avg_job_duration_by_region()
    assert 'RU' in out and 'US' in out and 'IN' in out

def test_avg_job_duration_by_experience(analyzer):
    out = analyzer.avg_job_duration_by_experience()
    assert 'Expert' in out and 'Intermediate' in out and 'Beginner' in out

def test_avg_job_duration_by_platform(analyzer):
    out = analyzer.avg_job_duration_by_platform()
    assert 'Upwork' in out and 'Freelancer' in out

def test_avg_job_duration_by_project_type(analyzer):
    out = analyzer.avg_job_duration_by_project_type()
    assert 'Web' in out and 'Mobile' in out

def test_avg_income_by_platform(analyzer):
    out = analyzer.avg_income_by_platform()
    assert 'Upwork' in out and 'Freelancer' in out

def test_avg_income_by_project_type(analyzer):
    out = analyzer.avg_income_by_project_type()
    assert 'Web' in out and 'Mobile' in out

def test_avg_hourly_rate_by_category(analyzer):
    out = analyzer.avg_hourly_rate_by('category')
    assert 'Design' in out and 'Programming' in out

def test_avg_success_rate_by_category(analyzer):
    out = analyzer.avg_success_rate_by('category')
    assert 'Design' in out and 'Programming' in out

def test_avg_client_rating_by_category(analyzer):
    out = analyzer.avg_client_rating_by('category')
    assert 'Design' in out and 'Programming' in out

def test_avg_marketing_spend_by_category(analyzer):
    out = analyzer.avg_marketing_spend_by('category')
    assert 'Design' in out and 'Programming' in out 
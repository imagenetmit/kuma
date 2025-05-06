import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    # Set test-specific environment variables
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    os.environ['UPTIME_KUMA_DB_TYPE'] = 'mariadb'
    os.environ['UPTIME_KUMA_DB_HOSTNAME'] = 'localhost'
    os.environ['UPTIME_KUMA_DB_PORT'] = '3306'
    os.environ['UPTIME_KUMA_DB_NAME'] = 'test_db'
    os.environ['UPTIME_KUMA_DB_USERNAME'] = 'test_user'
    os.environ['UPTIME_KUMA_DB_PASSWORD'] = 'test_password'
    os.environ['NINJA_CLIENT_ID'] = 'test_client_id'
    os.environ['NINJA_CLIENT_SECRET'] = 'test_client_secret'
    os.environ['NINJA_TOKEN_URL'] = 'http://test.com/token'
    os.environ['NINJA_SCOPE'] = 'test_scope'
    os.environ['NINJA_API_BASE_URL'] = 'http://test.com/api'

# Configure pytest-cov to report on the right modules
def pytest_configure(config):
    config.option.cov_source = ['tcpresponder']
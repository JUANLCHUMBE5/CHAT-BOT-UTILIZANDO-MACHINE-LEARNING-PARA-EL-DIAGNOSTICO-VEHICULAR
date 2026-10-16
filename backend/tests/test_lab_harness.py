"""Regresiones del aislamiento del laboratorio y fixtures reutilizables."""
import pytest

from scripts.lab.safety import require_lab_environment
from scripts.lab.scenarios import SCENARIOS


def safe():
    return {'CARBOT_LAB_ENABLED': 'true', 'ENVIRONMENT': 'test', 'CARBOT_BLOCK_DOTENV': 'true',
            'DATABASE_URL': 'postgresql://test:test@postgres:5432/carbot_e2e',
            'REDIS_URL': 'redis://redis:6379/0'}


def test_lab_safe_environment():
    require_lab_environment(safe())


@pytest.mark.parametrize('key,value', [
    ('ENVIRONMENT', 'production'), ('CARBOT_LAB_ENABLED', 'false'),
    ('CARBOT_BLOCK_DOTENV', 'false'), ('GEMINI_API_KEY', 'synthetic-not-a-key'),
    ('GROQ_API_KEY', 'synthetic-not-a-key'), ('META_ACCESS_TOKEN', 'synthetic-not-a-token'),
    ('DATABASE_URL', 'postgresql://test:test@external:5432/carbot_e2e'),
    ('DATABASE_URL', 'postgresql://test:test@postgres:5432/production'),
    ('REDIS_URL', 'redis://external:6379/0'),
])
def test_lab_rejects_unsafe_environment(key, value):
    env = safe()
    env[key] = value
    with pytest.raises(RuntimeError):
        require_lab_environment(env)


def test_scenarios_are_separate_and_complete():
    assert {case['plate'] for case in SCENARIOS.values()} == {'ABC123', 'XYZ789'}
    assert len({case['phone'] for case in SCENARIOS.values()}) == 2
    assert all(len(case['turns']) == 5 for case in SCENARIOS.values())
    assert all('No generes otro diagnóstico' in case['turns'][-1] for case in SCENARIOS.values())

from datetime import date
from app.models.athlete import AthleteProfile


def test_age_property(monkeypatch):
    dob = date(2000, 1, 1)
    fake_today = date(2024, 1, 1)

    class MockDate(date):
        @classmethod
        def today(cls):
            return fake_today

    monkeypatch.setattr('datetime.date', MockDate)
    profile = AthleteProfile(date_of_birth=dob)
    assert profile.age == 24

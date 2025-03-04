from datetime import datetime, timedelta
import random
from .base import ReplacementStrategy

class DateReplacementStrategy(ReplacementStrategy):
    def __init__(self, start_date=datetime(1900,1,1), end_date=datetime(2100,12,31)):
        self.start_date = start_date
        self.end_date = end_date

    def replace(self, entity):
        delta = self.end_date - self.start_date
        random_days = random.randint(0, delta.days)
        random_date = self.start_date + timedelta(days=random_days)
        return random_date.strftime("%Y-%m-%d")
from datetime import datetime, timedelta
from tools.base import Tool
import locale


class CurrentDateTool(Tool):
    # def __init__(self):
    # Set locale for Russian month/day names
    # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    def description(self) -> str:
        return "Get current date in human readable format"

    def execute(self, **kwargs) -> dict:
        now = datetime.now()

        return {
            'date': now.strftime('%d-%m-%Y'),  # DD-MM-YYYY
            'weekday': now.strftime('%A'),  # Full weekday name
            # "01 января 2024, понедельник"
            'readable': now.strftime('%d %B %Y, %A')
        }


def next_thursday():
    # todays date
    today = datetime.today()
    days_ahead = 3 - today.weekday()  # 3 соответствует четвергу
    if days_ahead <= 0:
        days_ahead += 7  # если сегодня четверг или позже, вернём следующий четверг
    next_thursday_date = today + timedelta(days=days_ahead)
    # return next_thursday_date.strftime('%d-%m-%Y')
    return next_thursday_date

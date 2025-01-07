from datetime import datetime, timedelta
from unittest.mock import patch
import pytest
from src.tools.date import CurrentDateTool, next_thursday

@pytest.fixture
def date_tool():
    return CurrentDateTool()

def test_current_date_tool_description(date_tool):
    assert date_tool.description() == "Get current date in human readable format"

@patch('src.tools.date.datetime')
def test_current_date_tool_execute(mock_datetime, date_tool):
    # Use any date for testing
    mock_date = datetime.now()
    mock_datetime.now.return_value = mock_date

    result = date_tool.execute()
    
    assert result['date'] == mock_date.strftime('%d-%m-%Y')
    assert result['weekday'] == mock_date.strftime('%A')
    assert result['readable'] == mock_date.strftime('%d %B %Y, %A')

@patch('src.tools.date.datetime')
def test_next_thursday_from_any_day(mock_datetime):
    # Test for each day of the week
    for test_day in range(7):  # 0 = Monday, 6 = Sunday
        mock_date = datetime(2024, 1, 1) + timedelta(days=test_day)  # Start from Monday
        mock_datetime.today.return_value = mock_date

        result = next_thursday()
        
        # Calculate expected next Thursday
        days_until_thursday = (3 - test_day) % 7  # 3 represents Thursday
        if days_until_thursday <= 0:
            days_until_thursday += 7
            
        expected_date = mock_date + timedelta(days=days_until_thursday)
        assert result.strftime('%Y-%m-%d') == expected_date.strftime('%Y-%m-%d')

@patch('src.tools.date.datetime')
def test_next_thursday_consecutive_weeks(mock_datetime):
    # Test that calling next_thursday on a Thursday returns next week's Thursday
    mock_date = datetime(2024, 1, 4)  # A Thursday
    mock_datetime.today.return_value = mock_date
    
    result = next_thursday()
    expected_date = mock_date + timedelta(days=7)
    
    assert result.strftime('%Y-%m-%d') == expected_date.strftime('%Y-%m-%d')

import pytest
from src.scenarios.booking import BookingScenario
from src.planner import ProxyPlanner


class TestBookingScenario:
    @pytest.fixture
    def booking_scenario(self):
        return BookingScenario()

    @pytest.mark.parametrize("command,expected_score", [
        ("забронируй мне 3 аудитории на четверг", 1.0),
        ("забронируй аудиторию", 1.0),
        ("бронь на среду", 1.0),
        ("напиши пост", 0.0),
        ("создай событие", 0.0),
        ("позови модератора", 0.0),
    ])
    def test_booking_intent_classification(self, booking_scenario, command, expected_score):
        score = booking_scenario.classify_intent(command)
        assert score == expected_score


class TestProxyPlanner:
    @pytest.fixture
    def planner(self):
        return ProxyPlanner()

    @pytest.fixture
    def mock_scenario(self, mocker):
        scenario = mocker.Mock()
        scenario.__class__.__name__ = "MockScenario"
        return scenario

    def test_register_scenario(self, planner, mock_scenario):
        planner.register_scenario(mock_scenario)
        assert mock_scenario in planner.scenarios
        assert len(planner.scenarios) == 1

    def test_classify_and_select_no_scenarios(self, planner):
        with pytest.raises(RuntimeError, match="No scenarios registered"):
            planner.classify_and_select("test command")

    def test_classify_and_select_low_confidence(self, planner, mock_scenario):
        mock_scenario.classify_intent.return_value = 0.1
        planner.register_scenario(mock_scenario)

        with pytest.raises(ValueError, match="All scenarios returned low confidence scores"):
            planner.classify_and_select("test command")

    def test_classify_and_select_success(self, planner, mock_scenario):
        mock_scenario.classify_intent.return_value = 0.8
        planner.register_scenario(mock_scenario)

        selected_scenario, score = planner.classify_and_select("test command")
        assert selected_scenario == mock_scenario
        assert score == 0.8

    def test_classify_and_select_multiple_scenarios(self, planner, mocker):
        scenario1 = mocker.Mock()
        scenario1.__class__.__name__ = "Scenario1"
        scenario1.classify_intent.return_value = 0.8

        scenario2 = mocker.Mock()
        scenario2.__class__.__name__ = "Scenario2"
        scenario2.classify_intent.return_value = 0.4

        planner.register_scenario(scenario1)
        planner.register_scenario(scenario2)

        selected_scenario, score = planner.classify_and_select("test command")
        assert selected_scenario == scenario1
        assert score == 0.8

    def test_classify_and_select_similar_scores(self, planner, mocker, caplog):
        scenario1 = mocker.Mock()
        scenario1.__class__.__name__ = "Scenario1"
        scenario1.classify_intent.return_value = 0.85

        scenario2 = mocker.Mock()
        scenario2.__class__.__name__ = "Scenario2"
        scenario2.classify_intent.return_value = 0.82

        planner.register_scenario(scenario1)
        planner.register_scenario(scenario2)

        selected_scenario, score = planner.classify_and_select("test command")
        assert selected_scenario == scenario1
        assert score == 0.85
        assert "Multiple scenarios have similar scores" in caplog.text

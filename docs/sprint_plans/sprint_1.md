# LLM Agent System Technical Specification

## 1. Core Components
```bash
club_manager/
├── config.yaml         # All settings in one file
├── docker-compose.yml  # For running Redis and MongoDB
├── Dockerfile
├── src/
│   ├── nlu_manager.py # Main NLU manager
│   ├── planner.py     # ProxyPlanner
│   ├── view.py        # CLI view
│   ├── scenarios/
│   │   ├── __init__.py
│   │   ├── base.py    # Base scenario class
│   │   └── booking.py # Booking implementation
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── mongo_client.py
│   │   └── redis_client.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── browser.py # Playwright tools
│   └── __init__.py
├── tests/
│   ├── conftest.py    # pytest fixtures
│   ├── test_booking.py
│   └── test_nlu.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

### NLU Manager
The NLU Manager serves as the central coordinator of the entire system. It owns the view component and manages all interactions between user input and system execution.

In MVP, it processes natural language commands and handles clarification dialogues when scenarios require additional information. The manager maintains the active scenario state and coordinates all system responses through its view component. Future extensions of the manager could include context maintenance between commands, command history analysis, and learning from user patterns, coordinating many processes.

```python
class NLUManager:
    def __init__(self):
        self.view = CLIView()
        self.proxy_planner = ProxyPlanner()
        self.redis = Redis()
        self.active_scenario = None
        
    def process_command(self, command: str)
    def listen_for_messages(self)
    def run(self)
```

## View Component
The view component handles all visual interaction with the user through CLI in the MVP phase. It provides methods for displaying progress, errors, thinking processes, and capturing user input. The view has no business logic - it's purely responsible for input/output formatting and display. This clean separation allows for easy replacement with other interfaces (Telegram, Web) in the future.

```python
class CLIView
```

### Proxy Planner
The proxy planner determines which scenario should handle the user's command. It distributes commands to all registered scenarios for scoring and selects the highest-scoring scenario for execution. The scoring system uses stem-word matching in MVP (e.g., "брон" for booking-related commands) but can be enhanced with more sophisticated classification methods later.

```python
class ProxyPlanner:
    def classify_and_select(self, command: str) -> BaseScenario
    def register_scenario(self, scenario: BaseScenario)
```

### Scenario System
Each scenario (booking, moderator management, etc.) inherits from a base scenario class and implements specific automation logic. A scenario first attempts to execute a predefined sequence of steps, consulting its LLM brain only when encountering unexpected situations or needing decision support. Each scenario maintains its own state and toolset while following a common interface.

```python
class BaseScenario:
    def __init__(self):
        self.llm_brain = LLMBrain()
        self.state = ScenarioState()
        self.state_history = []
        self.tools = ScenarioToolbox()
    
    def classify_intent(self, command: str) -> float
    def execute(self, command: str)
    def continue_with_input(self, user_input: str)
    def check_success(self) -> bool

```
### Storage System
The storage system combines Redis for active state management and messaging with MongoDB for historical data and analytics. Redis handles immediate state tracking and inter-component communication, while MongoDB maintains comprehensive execution histories (in other words – history of states) and helps with pattern analysis for future optimizations. For examples it should store all the commands, responses, and states of the system, user answers to questions – this way later we can adapt it to resolve similar issues without user intervention.


## 2. Command Flow Example

Let's follow a typical command through the system: "забронируй 3 аудитории рядом в этот четверг"

1. The NLU interface receives the command and forwards it to the proxy planner.

2. The proxy planner distributes this command to all scenarios for scoring. Booking scenario returns the highest score (1) due to presence of "брон" stem and room-related keywords, getting selected for execution.

3. The booking scenario executes its predefined sequence:
   - Checks login status and logs in if needed
   - Navigates to the booking page
   - Selects necessary building in drop-out list and nearest Thursday in the calendar
   - Attempts to find adjacent available rooms (and decides which set of rooms will be booked)
   - Fill in the booking form with selected rooms and times for each room

4. During execution, the scenario encounters an unexpected state - say the selected building shows no available rooms. At this point, it consults its LLM brain, providing current webpage content, available tools, and action history. The LLM analyzes the situation and can take one of two paths:

   a) Handle the situation itself: LLM might decide to try booking in a different building, recognizing there are other options available. It would then use navigation tools to switch buildings and continue the booking process.

   b) Request user assistance: If no obvious solution exists, LLM formulates a clear question like "Все аудитории в главном здании заняты. Поискать в других корпусах или на другую дату?". The scenario pauses, waiting for user input through the NLU manager.

5. After receiving user confirmation to check "Чайковского" building, the scenario changes – LLM suggests to take few steps back and try to book rooms in another building – it creates new scenario which would be executed from the last successful step.

6. Upon completing the booking sequence, the scenario calls its check_success method, verifying that the bookings appear in the user's booking list with correct times and room numbers.

7. If there is more then 1 room needed, the scenario will repeat the booking process until all rooms are booked.

8. Finally, the NLU manager receives success confirmation and displays a summary to the user: "Забронированы аудитории 405, 406, 407 в здании на Чайковского на четверг."

## 3. Messaging System

NLUManager and Scenarios communicate through a messaging system built on Redis. The manager sends commands to scenarios and receives responses asynchronously. The system uses a simple pub/sub model with channels for each scenario, allowing for easy scaling and parallel execution of multiple scenarios.


## 4. State Management

State management takes place in Scenario class. The immediate scenario state tracks current state, all steps and results, current progress and context.

## 5. LLM Integration

The LLM integration is built around a common interface that supports multiple providers:

```python
class LLMInterface(ABC)
```

The LLM is consulted when scenarios encounter errors or unexpected states, receiving context about the current situation and available tools. It returns structured actions that the scenario manager can execute.

## 6. Development Requirements

- Python 3.10+
- Playwright handles browser automation with Chrome
- The system uses structured logging with different levels for debugging, user feedback, and error tracking.
- Test coverage focuses on tool reliability and scenario flow verification, with particular attention to error handling and recovery paths. Test should be triggered with simple CLI commands like `pytest tests/`.

## 7. Future Scalability

- more scenarios like moderator management and event organization.
- a fact persistence system will store learned preferences and patterns, such as preferred halls or common booking times
- The most ambitious extension is self-modifying tooling, where the LLM can propose and implement modifications to existing tools or create new tools based on observed patterns and requirements.
- etc
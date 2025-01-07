from typing import List, Tuple
from scenarios.base import BaseScenario
import logging

logger = logging.getLogger(__name__)

class ProxyPlanner:
    def __init__(self):
        self.scenarios: List[BaseScenario] = []
        self.MIN_CONFIDENCE_THRESHOLD = 0.3
        self.SIMILAR_SCORES_THRESHOLD = 0.1
    
    def register_scenario(self, scenario: BaseScenario) -> None:
        """Register a new scenario with the planner"""
        self.scenarios.append(scenario)
        logger.info(f"Registered scenario: {scenario.__class__.__name__}")
    
    def classify_and_select(self, command: str) -> Tuple[BaseScenario, float]:
        """
        Distribute command to all scenarios and select the highest scoring one
        Returns tuple of (selected_scenario, score)
        Raises:
            RuntimeError: If no scenarios registered
            ValueError: If all scores are below confidence threshold
            Warning: If multiple scenarios have similar high scores
        """
        if not self.scenarios:
            raise RuntimeError("No scenarios registered")
            
        # Get scores from all scenarios
        scored_scenarios = [
            (scenario, scenario.classify_intent(command))
            for scenario in self.scenarios
        ]
        
        # Find scenario with highest score
        selected_scenario, max_score = max(
            scored_scenarios,
            key=lambda x: x[1]
        )

        # Check if the best score is too low
        if max_score < self.MIN_CONFIDENCE_THRESHOLD:
            raise ValueError(
                f"All scenarios returned low confidence scores (best: {max_score:.2f})"
            )

        # Check for scenarios with similar scores
        similar_scenarios = [
            (s.__class__.__name__, score) 
            for s, score in scored_scenarios
            if abs(score - max_score) <= self.SIMILAR_SCORES_THRESHOLD 
            and s != selected_scenario
        ]
        
        if similar_scenarios:
            scenarios_list = ", ".join(
                f"{name}({score:.2f})" 
                for name, score in similar_scenarios
            )
            logger.warning(
                f"Multiple scenarios have similar scores to "
                f"{selected_scenario.__class__.__name__}({max_score:.2f}): {scenarios_list}"
            )
        
        logger.info(f"Selected scenario {selected_scenario.__class__.__name__} with score {max_score}")
        return selected_scenario, max_score
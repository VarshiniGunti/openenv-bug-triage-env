"""Dynamic grader for OpenEnv Bug Triage Environment."""

from models.action import BugAction
from models.scenario import BugScenario


class DynamicGrader:
    """Dynamic grader that evaluates agent output and returns variable scores."""
    
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float:
        """
        Grade the agent's action.
        
        Args:
            action: The agent's action
            scenario: The current scenario
            step: The current step number
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        
        # Step 1: Bug type classification
        if step == 1:
            if action.bug_type == scenario.ground_truth_type:
                score = 0.3
            else:
                score = 0.0
        
        # Step 2: File identification
        elif step == 2:
            if action.file == scenario.ground_truth_file:
                score = 0.3
            else:
                score = 0.0
        
        # Step 3: Fix proposal with semantic evaluation
        elif step == 3:
            # Keyword matching
            if self._keyword_match(action.fix, scenario.ground_truth_fix):
                score = 0.4
            # Semantic similarity
            elif self._semantic_similarity(action.fix, scenario.ground_truth_fix) >= 0.65:
                score = 0.3
            elif self._semantic_similarity(action.fix, scenario.ground_truth_fix) >= 0.45:
                score = 0.2
            elif self._semantic_similarity(action.fix, scenario.ground_truth_fix) >= 0.35:
                score = 0.1
            else:
                score = 0.0
        
        return min(max(score, 0.0), 1.0)
    
    def _keyword_match(self, proposed: str, ground_truth: str) -> bool:
        """Check if key tokens from ground truth appear in proposed fix."""
        proposed_tokens = set(proposed.lower().split())
        truth_tokens = set(ground_truth.lower().split())
        
        # Check if at least 50% of ground truth tokens are in proposed
        if len(truth_tokens) == 0:
            return False
        
        overlap = len(proposed_tokens & truth_tokens)
        return overlap / len(truth_tokens) >= 0.5
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using TF-IDF."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
            return float(similarity)
        except:
            # Fallback to simple token overlap
            tokens1 = set(text1.lower().split())
            tokens2 = set(text2.lower().split())
            
            if len(tokens1) == 0 or len(tokens2) == 0:
                return 0.0
            
            overlap = len(tokens1 & tokens2)
            return overlap / max(len(tokens1), len(tokens2))

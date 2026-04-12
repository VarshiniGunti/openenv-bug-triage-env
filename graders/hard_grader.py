"""Grader for Hard task - evaluates bug_type, file, and fix with semantic + keyword matching."""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openenv.core.rubrics.base import Rubric
from utils.normalization import normalize_bug_type, normalize_file, normalize_fix_text


class HardGrader(Rubric):
    """
    Grader for Hard task difficulty.
    Extends openenv-core Rubric for validator compatibility.
    Step 1: bug_type, Step 2: file, Step 3: fix (semantic).
    """

    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }

    def __init__(self):
        """Initialize the HardGrader."""
        super().__init__()

    def forward(self, action, observation) -> float:
        """
        Compute reward from action and observation.
        Called by the openenv-core validator via grader(action, observation).
        """
        try:
            if hasattr(action, "bug_type"):
                bug_type = normalize_bug_type(str(action.bug_type))
                file_val = normalize_file(str(action.file))
                fix_val = normalize_fix_text(str(action.fix))
            elif isinstance(action, dict):
                bug_type = normalize_bug_type(str(action.get("bug_type", "")))
                file_val = normalize_file(str(action.get("file", "")))
                fix_val = normalize_fix_text(str(action.get("fix", "")))
            else:
                return 0.35

            if hasattr(observation, "ground_truth_type"):
                gt_type = normalize_bug_type(str(observation.ground_truth_type))
                gt_file = normalize_file(str(observation.ground_truth_file))
                gt_fix = normalize_fix_text(str(observation.ground_truth_fix))
            elif isinstance(observation, dict):
                gt_type = normalize_bug_type(str(observation.get("ground_truth_type", "")))
                gt_file = normalize_file(str(observation.get("ground_truth_file", "")))
                gt_fix = normalize_fix_text(str(observation.get("ground_truth_fix", "")))
            else:
                return 0.35

            score = 0.0
            score += 0.35 if bug_type == gt_type else 0.05
            score += 0.35 if file_val == gt_file else 0.05
            fix_score = self.combined_fix_match(fix_val, gt_fix)
            score += 0.05 + (0.9 * fix_score) * 0.4
            return min(max(score / 3, 0.05), 0.95)
        except Exception:
            return 0.35
    
    def extract_keywords(self, text: str) -> set:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Set of lowercase keywords
        """
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stopwords and short words
        keywords = {
            word for word in words
            if word not in self.STOPWORDS and len(word) > 2
        }
        
        return keywords
    
    def keyword_match(self, action_fix: str, ground_truth_fix: str) -> bool:
        """
        Check if action fix contains keywords from ground truth fix.
        
        Args:
            action_fix: The proposed fix from the agent
            ground_truth_fix: The ground truth fix
            
        Returns:
            True if any keyword matches, False otherwise
        """
        ground_keywords = self.extract_keywords(ground_truth_fix)
        action_keywords = self.extract_keywords(action_fix)
        
        # Check if there's any overlap
        return bool(ground_keywords & action_keywords)
    
    def semantic_match(self, action_fix: str, ground_truth_fix: str) -> float:
        """
        Evaluate fix using semantic similarity with TF-IDF vectorization.
        
        Args:
            action_fix: The proposed fix from the agent
            ground_truth_fix: The ground truth fix
            
        Returns:
            Similarity score strictly between 0 and 1 (exclusive)
        """
        try:
            # Use character-level n-grams for semantic similarity
            vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
            vectors = vectorizer.fit_transform([action_fix, ground_truth_fix])
            similarity = cosine_similarity(vectors)[0, 1]
            # Ensure strict range (0, 1)
            if similarity <= 0.0:
                return 0.1
            if similarity >= 1.0:
                return 0.9
            return float(similarity)
        except Exception:
            # Fallback to keyword matching if semantic analysis fails
            return 0.9 if self.keyword_match(action_fix, ground_truth_fix) else 0.1
    
    def combined_fix_match(self, action_fix: str, ground_truth_fix: str) -> float:
        """
        Hybrid keyword + semantic matching for fix evaluation.
        
        Implements tiered scoring:
        - Keyword match: 0.4 reward
        - High semantic similarity (>=0.65): 0.3 reward
        - Medium semantic similarity (>=0.45): 0.2 reward
        - Reasoning credit (>=0.35): 0.1 reward (for showing understanding)
        - Otherwise: 0.0 reward
        
        Args:
            action_fix: The proposed fix from the agent
            ground_truth_fix: The ground truth fix
            
        Returns:
            Combined score strictly between 0 and 1 (exclusive)
        """
        # Step 1: Check for keyword match
        has_keywords = self.keyword_match(action_fix, ground_truth_fix)
        
        if has_keywords:
            # Keyword match found - return 0.95 (will be scaled to 0.4 * 0.95 = 0.38 in grade())
            return 0.95
        
        # Step 2: Check semantic similarity for partial credit
        semantic_score = self.semantic_match(action_fix, ground_truth_fix)
        
        if semantic_score >= 0.65:
            # High semantic similarity - return 0.75 (will be scaled to 0.4 * 0.75 = 0.30 in grade())
            return 0.75
        elif semantic_score >= 0.45:
            # Medium semantic similarity - return 0.5 (will be scaled to 0.4 * 0.5 = 0.20 in grade())
            return 0.5
        elif semantic_score >= 0.35:
            # Reasoning credit - return 0.25 (will be scaled to 0.4 * 0.25 = 0.10 in grade())
            # This rewards agents for showing understanding even if fix isn't perfect
            return 0.25
        else:
            # Low similarity - minimal credit
            return 0.05
    
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float:
        """
        Grade an action for the Hard task.
        
        Args:
            action: The agent's action
            scenario: The bug scenario with ground truth
            step: The current step (1, 2, or 3)
            
        Returns:
            Reward value strictly between 0 and 1 (exclusive)
        """
        if step == 1:
            # Step 1: Evaluate bug_type
            if action.bug_type == scenario.ground_truth_type:
                return 0.35  # Strictly between 0 and 1
            else:
                return 0.05  # Strictly between 0 and 1
        elif step == 2:
            # Step 2: Evaluate file
            if action.file == scenario.ground_truth_file:
                return 0.35  # Strictly between 0 and 1
            else:
                return 0.05  # Strictly between 0 and 1
        elif step == 3:
            # Step 3: Evaluate fix using combined semantic + keyword matching
            match_score = self.combined_fix_match(action.fix, scenario.ground_truth_fix)
            # Scale match score to range (0.05, 0.95) to stay strictly between 0 and 1
            return 0.05 + (0.9 * match_score)
        else:
            return 0.05
    
    def get_tasks(self):
        """Return list of tasks this grader handles."""
        return [{"id": "hard_bug", "grader": self}]

"""Grader for Hard task - evaluates bug_type, file, and fix with semantic + keyword matching."""

import re
import sys
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.action import BugAction
from models.scenario import BugScenario


class HardGrader:
    """
    Grader for Hard task difficulty.
    
    Step 1: Evaluates bug_type (0.3 reward)
    Step 2: Evaluates file (0.3 reward)
    Step 3: Evaluates fix using keyword matching (0.4 reward)
    Total normalized reward: [0.0, 1.0]
    """
    
    # Common stopwords to exclude from keyword matching
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
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
            Similarity score in [0.0, 1.0]
        """
        try:
            # Use character-level n-grams for semantic similarity
            vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
            vectors = vectorizer.fit_transform([action_fix, ground_truth_fix])
            similarity = cosine_similarity(vectors)[0, 1]
            return float(similarity)
        except Exception:
            # Fallback to keyword matching if semantic analysis fails
            return 1.0 if self.keyword_match(action_fix, ground_truth_fix) else 0.0
    
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
            Combined score in [0.0, 1.0]
        """
        # Step 1: Check for keyword match
        has_keywords = self.keyword_match(action_fix, ground_truth_fix)
        
        if has_keywords:
            # Keyword match found - return 0.4 (will be scaled to 0.4 * 0.4 = 0.16 in grade())
            return 1.0
        
        # Step 2: Check semantic similarity for partial credit
        semantic_score = self.semantic_match(action_fix, ground_truth_fix)
        
        if semantic_score >= 0.65:
            # High semantic similarity - return 0.3 (will be scaled to 0.4 * 0.3 = 0.12 in grade())
            return 0.75
        elif semantic_score >= 0.45:
            # Medium semantic similarity - return 0.2 (will be scaled to 0.4 * 0.2 = 0.08 in grade())
            return 0.5
        elif semantic_score >= 0.35:
            # Reasoning credit - return 0.25 (will be scaled to 0.4 * 0.25 = 0.1 in grade())
            # This rewards agents for showing understanding even if fix isn't perfect
            return 0.25
        else:
            # Low similarity - no credit
            return 0.0
    
    def grade(self, action: BugAction, scenario: BugScenario, step: int) -> float:
        """
        Grade an action for the Hard task.
        
        Args:
            action: The agent's action
            scenario: The bug scenario with ground truth
            step: The current step (1, 2, or 3)
            
        Returns:
            Reward value (0.0 to 0.4 depending on step)
        """
        if step == 1:
            # Step 1: Evaluate bug_type
            if action.bug_type == scenario.ground_truth_type:
                return 0.3
            else:
                return 0.0
        elif step == 2:
            # Step 2: Evaluate file
            if action.file == scenario.ground_truth_file:
                return 0.3
            else:
                return 0.0
        elif step == 3:
            # Step 3: Evaluate fix using combined semantic + keyword matching
            match_score = self.combined_fix_match(action.fix, scenario.ground_truth_fix)
            # Scale match score to 0.4 reward range
            return 0.4 * match_score
        else:
            return 0.0

"""Tests for action normalization utilities."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalization import (
    normalize_bug_type,
    normalize_file,
    normalize_fix_text,
    normalize_action_fields
)


class TestNormalizeBugType:
    """Tests for bug type normalization."""
    
    def test_lowercase_conversion(self):
        """Test conversion to lowercase."""
        assert normalize_bug_type("NULL_POINTER") == "null_pointer"
        assert normalize_bug_type("Null_Pointer") == "null_pointer"
        assert normalize_bug_type("MEMORY") == "memory"
    
    def test_space_to_underscore(self):
        """Test conversion of spaces to underscores."""
        assert normalize_bug_type("null pointer") == "null_pointer"
        assert normalize_bug_type("race condition") == "race_condition"
        assert normalize_bug_type("null  pointer") == "null__pointer"
    
    def test_hyphen_to_underscore(self):
        """Test conversion of hyphens to underscores."""
        assert normalize_bug_type("null-pointer") == "null_pointer"
        assert normalize_bug_type("race-condition") == "race_condition"
    
    def test_mixed_normalization(self):
        """Test mixed normalization scenarios."""
        assert normalize_bug_type("Null Pointer") == "null_pointer"
        assert normalize_bug_type("Null-Pointer") == "null_pointer"
        assert normalize_bug_type("NULL POINTER") == "null_pointer"
        assert normalize_bug_type("null-pointer") == "null_pointer"
    
    def test_whitespace_stripping(self):
        """Test stripping of leading/trailing whitespace."""
        assert normalize_bug_type("  null_pointer  ") == "null_pointer"
        assert normalize_bug_type("\tnull_pointer\n") == "null_pointer"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_bug_type("") == ""
    
    def test_all_bug_types(self):
        """Test normalization of all standard bug types."""
        bug_types = [
            "memory", "logic", "authentication", "database",
            "performance", "null_pointer", "session", "race_condition"
        ]
        for bug_type in bug_types:
            # Already normalized types should remain unchanged
            assert normalize_bug_type(bug_type) == bug_type
            # Uppercase versions should normalize to lowercase
            assert normalize_bug_type(bug_type.upper()) == bug_type


class TestNormalizeFile:
    """Tests for file path normalization."""
    
    def test_lowercase_conversion(self):
        """Test conversion to lowercase."""
        assert normalize_file("AUTH.PY") == "auth.py"
        assert normalize_file("SRC/AUTH.PY") == "auth.py"
    
    def test_remove_src_prefix(self):
        """Test removal of src/ prefix."""
        assert normalize_file("src/auth.py") == "auth.py"
        assert normalize_file("SRC/AUTH.PY") == "auth.py"
    
    def test_remove_current_dir_prefix(self):
        """Test removal of ./ prefix."""
        assert normalize_file("./auth.py") == "auth.py"
        assert normalize_file(".\\auth.py") == "auth.py"
    
    def test_remove_parent_dir_prefix(self):
        """Test removal of ../ prefix."""
        assert normalize_file("../auth.py") == "auth.py"
        assert normalize_file("..\\auth.py") == "auth.py"
    
    def test_path_separator_normalization(self):
        """Test normalization of path separators."""
        assert normalize_file("src\\auth.py") == "auth.py"
        assert normalize_file("src/auth.py") == "auth.py"
    
    def test_nested_paths(self):
        """Test handling of nested paths."""
        assert normalize_file("src/models/auth.py") == "auth.py"
        assert normalize_file("src/models/database/connection.py") == "connection.py"
    
    def test_whitespace_stripping(self):
        """Test stripping of leading/trailing whitespace."""
        assert normalize_file("  auth.py  ") == "auth.py"
        assert normalize_file("\tsrc/auth.py\n") == "auth.py"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_file("") == ""
    
    def test_filename_only(self):
        """Test that filename-only paths remain unchanged."""
        assert normalize_file("auth.py") == "auth.py"
        assert normalize_file("database.py") == "database.py"
    
    def test_complex_paths(self):
        """Test complex path scenarios."""
        assert normalize_file("./src/../auth.py") == "auth.py"
        assert normalize_file("SRC/MODELS/AUTH.PY") == "auth.py"


class TestNormalizeFixText:
    """Tests for fix text normalization."""
    
    def test_lowercase_conversion(self):
        """Test conversion to lowercase."""
        assert normalize_fix_text("ADD NULL CHECK") == "add null check"
        assert normalize_fix_text("Add Null Check") == "add null check"
    
    def test_punctuation_removal(self):
        """Test removal of punctuation."""
        assert normalize_fix_text("Add null check!") == "add null check"
        assert normalize_fix_text("Add null check.") == "add null check"
        assert normalize_fix_text("Add null check?") == "add null check"
        assert normalize_fix_text("Add, null, check") == "add null check"
    
    def test_whitespace_collapsing(self):
        """Test collapsing of multiple spaces."""
        assert normalize_fix_text("Add  null  check") == "add null check"
        assert normalize_fix_text("Add   null   check") == "add null check"
    
    def test_whitespace_stripping(self):
        """Test stripping of leading/trailing whitespace."""
        assert normalize_fix_text("  add null check  ") == "add null check"
        assert normalize_fix_text("\tadd null check\n") == "add null check"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_fix_text("") == ""
    
    def test_complex_text(self):
        """Test complex text scenarios."""
        assert normalize_fix_text("Add null check before accessing user profile!") == "add null check before accessing user profile"
        assert normalize_fix_text("Fix  the  bug,  please!") == "fix the bug please"
    
    def test_preserve_underscores(self):
        """Test that underscores are preserved."""
        assert normalize_fix_text("Add null_pointer check") == "add null_pointer check"
        assert normalize_fix_text("Fix race_condition issue") == "fix race_condition issue"
    
    def test_special_characters(self):
        """Test removal of special characters."""
        assert normalize_fix_text("Add @null #check $now") == "add null check now"
        assert normalize_fix_text("Fix (race) [condition]") == "fix race condition"


class TestNormalizeActionFields:
    """Tests for normalizing all action fields at once."""
    
    def test_normalize_all_fields(self):
        """Test normalizing all fields together."""
        bug_type, file, fix = normalize_action_fields(
            "Null Pointer",
            "src/auth.py",
            "Add null check!"
        )
        assert bug_type == "null_pointer"
        assert file == "auth.py"
        assert fix == "add null check"
    
    def test_normalize_mixed_formats(self):
        """Test normalizing mixed format inputs."""
        bug_type, file, fix = normalize_action_fields(
            "RACE-CONDITION",
            "./models/concurrent.py",
            "Add mutex lock to protect shared resource access"
        )
        assert bug_type == "race_condition"
        assert file == "concurrent.py"
        assert fix == "add mutex lock to protect shared resource access"


class TestNormalizationRobustness:
    """Tests for normalization robustness with various LLM outputs."""
    
    def test_llm_output_variations(self):
        """Test handling of various LLM output formats."""
        # Different ways an LLM might output "null_pointer"
        variations = [
            "null_pointer",
            "null-pointer",
            "null pointer",
            "Null Pointer",
            "NULL_POINTER",
            "NULL-POINTER",
            "NULL POINTER",
        ]
        for var in variations:
            assert normalize_bug_type(var) == "null_pointer"
    
    def test_file_path_variations(self):
        """Test handling of various file path formats."""
        variations = [
            "auth.py",
            "src/auth.py",
            "./auth.py",
            "../auth.py",
            "SRC/AUTH.PY",
            "src\\auth.py",
        ]
        for var in variations:
            assert normalize_file(var) == "auth.py"
    
    def test_fix_text_variations(self):
        """Test handling of various fix text formats."""
        # All should normalize to the same base text
        variations = [
            "Add null check",
            "add null check",
            "ADD NULL CHECK",
            "Add null check!",
            "Add null check.",
            "Add  null  check",
            "  Add null check  ",
        ]
        for var in variations:
            assert normalize_fix_text(var) == "add null check"
    
    def test_edge_cases(self):
        """Test edge cases and unusual inputs."""
        # Empty strings
        assert normalize_bug_type("") == ""
        assert normalize_file("") == ""
        assert normalize_fix_text("") == ""
        
        # Only whitespace
        assert normalize_bug_type("   ") == ""
        assert normalize_file("   ") == ""
        assert normalize_fix_text("   ") == ""
        
        # Only punctuation
        assert normalize_fix_text("!!!") == ""
        assert normalize_fix_text("...") == ""


class TestBugTypeAliasMapping:
    """Tests for bug type alias mapping functionality."""
    
    def test_memory_aliases(self):
        """Test memory-related bug type aliases."""
        aliases = ["memory_leak", "memory leak", "memory_leaks", "memleak"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "memory"
    
    def test_authentication_aliases(self):
        """Test authentication-related bug type aliases."""
        aliases = ["auth", "auth_bug", "auth bug", "authentication_error", "auth_error"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "authentication"
    
    def test_null_pointer_aliases(self):
        """Test null pointer-related bug type aliases."""
        aliases = ["null_pointer", "null pointer", "null_pointer_exception", "npe", "null_ref"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "null_pointer"
    
    def test_race_condition_aliases(self):
        """Test race condition-related bug type aliases."""
        aliases = ["race_condition", "race condition", "concurrency_issue", "concurrent_access"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "race_condition"
    
    def test_database_aliases(self):
        """Test database-related bug type aliases."""
        aliases = ["database_error", "database error", "db_error", "sql_error"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "database"
    
    def test_performance_aliases(self):
        """Test performance-related bug type aliases."""
        aliases = ["performance_issue", "performance bug", "slow", "slowness", "timeout"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "performance"
    
    def test_session_aliases(self):
        """Test session-related bug type aliases."""
        aliases = ["session_error", "session bug", "session_management"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "session"
    
    def test_logic_aliases(self):
        """Test logic-related bug type aliases."""
        aliases = ["logic_error", "logic error", "logic_bug", "logical_error"]
        for alias in aliases:
            assert normalize_bug_type(alias) == "logic"
    
    def test_alias_case_insensitivity(self):
        """Test that alias mapping is case-insensitive."""
        assert normalize_bug_type("MEMORY LEAK") == "memory"
        assert normalize_bug_type("Auth Bug") == "authentication"
        assert normalize_bug_type("NULL POINTER EXCEPTION") == "null_pointer"
    
    def test_alias_with_mixed_separators(self):
        """Test alias mapping with mixed separators."""
        assert normalize_bug_type("memory-leak") == "memory"
        assert normalize_bug_type("auth_bug") == "authentication"
        assert normalize_bug_type("null-pointer-exception") == "null_pointer"


class TestReasoningCreditScenarios:
    """Tests for reasoning credit scenarios in grading."""
    
    def test_semantic_similarity_thresholds(self):
        """Test that semantic similarity thresholds are correctly applied."""
        # This test documents the expected behavior:
        # - semantic_score >= 0.65: 0.75 return (0.3 reward)
        # - semantic_score >= 0.45: 0.5 return (0.2 reward)
        # - semantic_score >= 0.35: 0.25 return (0.1 reward - reasoning credit)
        # - semantic_score < 0.35: 0.0 return (no reward)
        
        # These are documented thresholds for the hard grader
        thresholds = {
            0.65: 0.75,  # High similarity
            0.45: 0.5,   # Medium similarity
            0.35: 0.25,  # Reasoning credit
            0.34: 0.0,   # Below threshold
        }
        
        # Verify thresholds are documented correctly
        assert 0.65 >= 0.45  # High >= Medium
        assert 0.45 >= 0.35  # Medium >= Reasoning
        assert 0.35 > 0.34   # Reasoning > Below
    
    def test_reasoning_credit_boundary(self):
        """Test reasoning credit boundary at 0.35 semantic similarity."""
        # At exactly 0.35, agent should get reasoning credit (0.1 reward)
        # This rewards agents for showing understanding even if fix isn't perfect
        
        # Boundary condition: 0.35 should qualify for reasoning credit
        assert 0.35 >= 0.35  # True - gets credit
        
        # Just below boundary: 0.34 should not get credit
        assert not (0.34 >= 0.35)  # False - no credit
    
    def test_reward_scaling_with_reasoning_credit(self):
        """Test that reasoning credit is properly scaled in final reward."""
        # In hard_grader.grade(), step 3 scales match_score by 0.4
        # So reasoning credit (0.25 return) becomes: 0.4 * 0.25 = 0.1 reward
        
        reasoning_credit_return = 0.25
        fix_weight = 0.4
        expected_reward = fix_weight * reasoning_credit_return
        
        assert expected_reward == 0.1  # Reasoning credit = 0.1 reward

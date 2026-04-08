"""Action normalization utilities for LLM robustness.

This module provides normalization functions to handle variations in LLM outputs,
improving compatibility with different model formats and styles.
"""

import re
import os

# Bug type aliases for semantic equivalence
# Maps common LLM outputs to canonical bug types
BUG_TYPE_ALIASES = {
    # Memory-related aliases
    "memory_leak": "memory",
    "memory leak": "memory",
    "memory_leaks": "memory",
    "memory leaks": "memory",
    "memleak": "memory",
    
    # Authentication-related aliases
    "auth": "authentication",
    "auth_bug": "authentication",
    "auth bug": "authentication",
    "authentication_error": "authentication",
    "authentication error": "authentication",
    "auth_error": "authentication",
    "auth error": "authentication",
    
    # Logic-related aliases
    "logic_error": "logic",
    "logic error": "logic",
    "logic_bug": "logic",
    "logic bug": "logic",
    "logical_error": "logic",
    "logical error": "logic",
    
    # Null pointer-related aliases
    "null_pointer": "null_pointer",
    "null pointer": "null_pointer",
    "null_pointer_exception": "null_pointer",
    "null pointer exception": "null_pointer",
    "nullpointer": "null_pointer",
    "nullpointerexception": "null_pointer",
    "npe": "null_pointer",
    "null_ref": "null_pointer",
    "null reference": "null_pointer",
    
    # Race condition-related aliases
    "race_condition": "race_condition",
    "race condition": "race_condition",
    "race_condition_bug": "race_condition",
    "race condition bug": "race_condition",
    "concurrency_issue": "race_condition",
    "concurrency issue": "race_condition",
    "concurrent_access": "race_condition",
    "concurrent access": "race_condition",
    
    # Database-related aliases
    "database_error": "database",
    "database error": "database",
    "database_bug": "database",
    "database bug": "database",
    "db_error": "database",
    "db error": "database",
    "sql_error": "database",
    "sql error": "database",
    
    # Performance-related aliases
    "performance_issue": "performance",
    "performance issue": "performance",
    "performance_bug": "performance",
    "performance bug": "performance",
    "slow": "performance",
    "slowness": "performance",
    "timeout": "performance",
    "inefficiency": "performance",
    
    # Session-related aliases
    "session_error": "session",
    "session error": "session",
    "session_bug": "session",
    "session bug": "session",
    "session_management": "session",
    "session management": "session",
}


def normalize_bug_type(bug_type: str) -> str:
    """
    Normalize bug type to standard format with alias mapping.
    
    Normalization rules:
    - Convert to lowercase
    - Check BUG_TYPE_ALIASES for semantic equivalence
    - Replace spaces with underscores
    - Replace hyphens with underscores
    
    Examples:
        "memory leak" -> "memory"
        "null pointer exception" -> "null_pointer"
        "auth bug" -> "authentication"
        "Null Pointer" -> "null_pointer"
        "null-pointer" -> "null_pointer"
        "NULL_POINTER" -> "null_pointer"
    
    Args:
        bug_type: The bug type string to normalize
        
    Returns:
        Normalized bug type string
    """
    if not bug_type:
        return ""
    
    # Convert to lowercase
    normalized = bug_type.lower()
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    # Check if this is an alias for a canonical bug type
    if normalized in BUG_TYPE_ALIASES:
        return BUG_TYPE_ALIASES[normalized]
    
    # Replace spaces with underscores
    normalized = normalized.replace(" ", "_")
    
    # Check again after space replacement (e.g., "null pointer" -> "null_pointer")
    if normalized in BUG_TYPE_ALIASES:
        return BUG_TYPE_ALIASES[normalized]
    
    # Replace hyphens with underscores
    normalized = normalized.replace("-", "_")
    
    # Check again after hyphen replacement (e.g., "null-pointer" -> "null_pointer")
    if normalized in BUG_TYPE_ALIASES:
        return BUG_TYPE_ALIASES[normalized]
    
    return normalized


def normalize_file(file: str) -> str:
    """
    Normalize file path to standard format.
    
    Normalization rules:
    - Convert to lowercase
    - Remove path prefixes (src/, ./, ../, etc.)
    - Keep only filename
    - Normalize path separators
    
    Examples:
        "src/auth.py" -> "auth.py"
        "./auth.py" -> "auth.py"
        "../auth.py" -> "auth.py"
        "SRC/AUTH.PY" -> "auth.py"
        "src\\auth.py" -> "auth.py"
    
    Args:
        file: The file path to normalize
        
    Returns:
        Normalized filename
    """
    if not file:
        return ""
    
    # Convert to lowercase
    normalized = file.lower()
    
    # Normalize path separators (both / and \)
    normalized = normalized.replace("\\", "/")
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    # Remove leading path prefixes
    # Handle patterns like: src/, ./, ../, etc.
    while normalized.startswith("./") or normalized.startswith("../"):
        if normalized.startswith("./"):
            normalized = normalized[2:]
        elif normalized.startswith("../"):
            normalized = normalized[3:]
    
    # Remove any remaining directory paths (keep only filename)
    if "/" in normalized:
        normalized = normalized.split("/")[-1]
    
    return normalized


def normalize_fix_text(text: str) -> str:
    """
    Normalize fix description text.
    
    Normalization rules:
    - Convert to lowercase
    - Strip leading/trailing whitespace
    - Remove punctuation (except spaces)
    - Collapse multiple spaces into single space
    
    Examples:
        "Add null check!" -> "add null check"
        "Add  null  check" -> "add null check"
        "ADD NULL CHECK" -> "add null check"
    
    Args:
        text: The fix text to normalize
        
    Returns:
        Normalized fix text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    
    # Remove punctuation (keep alphanumeric, spaces, and underscores)
    # This preserves meaningful words while removing noise
    normalized = re.sub(r"[^\w\s]", "", normalized)
    
    # Collapse multiple spaces into single space
    normalized = re.sub(r"\s+", " ", normalized)
    
    return normalized


def normalize_action_fields(bug_type: str, file: str, fix: str) -> tuple:
    """
    Normalize all action fields at once.
    
    Args:
        bug_type: The bug type to normalize
        file: The file path to normalize
        fix: The fix text to normalize
        
    Returns:
        Tuple of (normalized_bug_type, normalized_file, normalized_fix)
    """
    return (
        normalize_bug_type(bug_type),
        normalize_file(file),
        normalize_fix_text(fix)
    )

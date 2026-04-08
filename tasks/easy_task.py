"""Easy task dataset with 14 bug scenarios."""

EASY_SCENARIOS = [
    {
        "bug_report": "Application crashes when user clicks the login button. Error message shows 'NullPointerException in auth module'.",
        "ground_truth_type": "null_pointer",
        "ground_truth_file": "auth.py",
        "ground_truth_fix": "Add null check before accessing user credentials",
        "repo_modules": ["auth.py", "user.py", "database.py", "config.py"],
        "difficulty": "easy",
        "scenario_id": "easy_01"
    },
    {
        "bug_report": "Database queries are extremely slow, taking 30+ seconds to complete. The application becomes unresponsive.",
        "ground_truth_type": "performance",
        "ground_truth_file": "database.py",
        "ground_truth_fix": "Add database indexes on frequently queried columns",
        "repo_modules": ["database.py", "models.py", "cache.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_02"
    },
    {
        "bug_report": "Users report that their session expires immediately after login. They have to log in again after every page refresh.",
        "ground_truth_type": "session",
        "ground_truth_file": "session.py",
        "ground_truth_fix": "Fix session cookie expiration time configuration",
        "repo_modules": ["session.py", "auth.py", "middleware.py", "config.py"],
        "difficulty": "easy",
        "scenario_id": "easy_03"
    },
    {
        "bug_report": "Memory usage grows continuously and never decreases. After 1 hour of use, the application uses 2GB of RAM.",
        "ground_truth_type": "memory",
        "ground_truth_file": "cache.py",
        "ground_truth_fix": "Implement proper cache eviction policy",
        "repo_modules": ["cache.py", "memory.py", "utils.py", "config.py"],
        "difficulty": "easy",
        "scenario_id": "easy_04"
    },
    {
        "bug_report": "Login fails for users with special characters in their password. Regular passwords work fine.",
        "ground_truth_type": "authentication",
        "ground_truth_file": "auth.py",
        "ground_truth_fix": "Properly escape special characters in password validation",
        "repo_modules": ["auth.py", "validation.py", "security.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_05"
    },
    {
        "bug_report": "Reports show incorrect totals. When adding 100 + 200, the result shows 300 sometimes and 250 other times.",
        "ground_truth_type": "logic",
        "ground_truth_file": "calculator.py",
        "ground_truth_fix": "Fix floating point precision in arithmetic operations",
        "repo_modules": ["calculator.py", "math.py", "utils.py", "validation.py"],
        "difficulty": "easy",
        "scenario_id": "easy_06"
    },
    {
        "bug_report": "Database connection fails with 'Access Denied' error. The application cannot retrieve any data.",
        "ground_truth_type": "database",
        "ground_truth_file": "database.py",
        "ground_truth_fix": "Update database credentials in connection string",
        "repo_modules": ["database.py", "config.py", "models.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_07"
    },
    {
        "bug_report": "Two concurrent requests cause data corruption. Running the same operation sequentially works correctly.",
        "ground_truth_type": "race_condition",
        "ground_truth_file": "concurrent.py",
        "ground_truth_fix": "Add mutex lock to protect shared resource access",
        "repo_modules": ["concurrent.py", "threading.py", "utils.py", "models.py"],
        "difficulty": "easy",
        "scenario_id": "easy_08"
    },
    {
        "bug_report": "Admin users cannot access the admin panel. Error shows 'Permission Denied' even though they have admin role.",
        "ground_truth_type": "authentication",
        "ground_truth_file": "permissions.py",
        "ground_truth_fix": "Fix role-based access control check logic",
        "repo_modules": ["permissions.py", "auth.py", "roles.py", "middleware.py"],
        "difficulty": "easy",
        "scenario_id": "easy_09"
    },
    {
        "bug_report": "The application crashes with 'SQL injection detected' error when users search for products with special characters like quotes or semicolons.",
        "ground_truth_type": "database",
        "ground_truth_file": "search.py",
        "ground_truth_fix": "Use parameterized queries instead of string concatenation",
        "repo_modules": ["search.py", "database.py", "query.py", "validation.py"],
        "difficulty": "easy",
        "scenario_id": "easy_10"
    },
    {
        "bug_report": "File upload fails with 'Permission denied' error. The uploaded files cannot be written to disk even though the directory exists.",
        "ground_truth_type": "database",
        "ground_truth_file": "file_upload.py",
        "ground_truth_fix": "Fix file permissions on upload directory",
        "repo_modules": ["file_upload.py", "storage.py", "config.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_11"
    },
    {
        "bug_report": "The payment processing endpoint returns 'Timeout' error intermittently. The same request works sometimes and fails other times.",
        "ground_truth_type": "performance",
        "ground_truth_file": "payment.py",
        "ground_truth_fix": "Increase timeout threshold for external payment API calls",
        "repo_modules": ["payment.py", "api.py", "config.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_12"
    },
    {
        "bug_report": "User notifications are not being sent. The notification queue appears to be stuck and messages are not being processed.",
        "ground_truth_type": "logic",
        "ground_truth_file": "notification_queue.py",
        "ground_truth_fix": "Fix queue processing logic to handle empty queue correctly",
        "repo_modules": ["notification_queue.py", "queue.py", "messaging.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_13"
    },
    {
        "bug_report": "The API returns 'Invalid token' error for valid authentication tokens. The token validation logic appears to be broken.",
        "ground_truth_type": "authentication",
        "ground_truth_file": "token_validator.py",
        "ground_truth_fix": "Fix token expiration check to use correct timestamp comparison",
        "repo_modules": ["token_validator.py", "auth.py", "security.py", "utils.py"],
        "difficulty": "easy",
        "scenario_id": "easy_14"
    }
]

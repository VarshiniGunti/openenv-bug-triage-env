"""Medium task dataset with 14 bug scenarios."""

MEDIUM_SCENARIOS = [
    {
        "bug_report": "User profile page loads but shows 'undefined' for the user's email address. Other fields display correctly. The email field is retrieved from the user service.",
        "ground_truth_type": "null_pointer",
        "ground_truth_file": "user_service.py",
        "ground_truth_fix": "Add null check for email field before rendering",
        "repo_modules": ["user_service.py", "profile.py", "api.py", "models.py", "cache.py", "database.py", "utils.py", "validation.py", "middleware.py", "config.py"],
        "difficulty": "medium",
        "scenario_id": "medium_01"
    },
    {
        "bug_report": "Search functionality returns results in 5 seconds for 100 items but 45 seconds for 1000 items. The query complexity appears to be O(n²).",
        "ground_truth_type": "performance",
        "ground_truth_file": "search_engine.py",
        "ground_truth_fix": "Optimize search algorithm to use binary search instead of linear search",
        "repo_modules": ["search_engine.py", "indexing.py", "database.py", "cache.py", "query.py", "models.py", "utils.py", "api.py", "middleware.py", "config.py"],
        "difficulty": "medium",
        "scenario_id": "medium_02"
    },
    {
        "bug_report": "Session data is lost when the user navigates between different subdomains. The session works fine within a single subdomain.",
        "ground_truth_type": "session",
        "ground_truth_file": "session_manager.py",
        "ground_truth_fix": "Configure session cookie domain to support all subdomains",
        "repo_modules": ["session_manager.py", "auth.py", "middleware.py", "config.py", "utils.py", "models.py", "database.py", "cache.py", "api.py", "security.py"],
        "difficulty": "medium",
        "scenario_id": "medium_03"
    },
    {
        "bug_report": "Memory usage increases by 50MB every time a report is generated. After generating 20 reports, the application uses 1GB of RAM.",
        "ground_truth_type": "memory",
        "ground_truth_file": "report_generator.py",
        "ground_truth_fix": "Release temporary data structures after report generation",
        "repo_modules": ["report_generator.py", "data_processor.py", "memory_manager.py", "utils.py", "models.py", "database.py", "cache.py", "api.py", "config.py", "middleware.py"],
        "difficulty": "medium",
        "scenario_id": "medium_04"
    },
    {
        "bug_report": "Two-factor authentication fails for users with certain phone numbers. The error message indicates an issue with SMS delivery.",
        "ground_truth_type": "session",
        "ground_truth_file": "two_factor_auth.py",
        "ground_truth_fix": "Fix phone number formatting before sending SMS",
        "repo_modules": ["two_factor_auth.py", "sms_service.py", "auth.py", "validation.py", "models.py", "utils.py", "api.py", "database.py", "config.py", "middleware.py"],
        "difficulty": "medium",
        "scenario_id": "medium_05"
    },
    {
        "bug_report": "Discount calculation shows different results depending on the order of operations. Applying 10% then 20% gives different result than 20% then 10%.",
        "ground_truth_type": "logic",
        "ground_truth_file": "pricing.py",
        "ground_truth_fix": "Fix discount calculation to apply discounts in correct order",
        "repo_modules": ["pricing.py", "cart.py", "products.py", "utils.py", "models.py", "validation.py", "api.py", "database.py", "cache.py", "config.py"],
        "difficulty": "medium",
        "scenario_id": "medium_06"
    },
    {
        "bug_report": "Database connection pool exhausts after running for a few hours. New queries fail with 'No available connections' error.",
        "ground_truth_type": "database",
        "ground_truth_file": "connection_pool.py",
        "ground_truth_fix": "Ensure database connections are properly closed after use",
        "repo_modules": ["connection_pool.py", "database.py", "models.py", "query.py", "utils.py", "api.py", "middleware.py", "config.py", "cache.py", "monitoring.py"],
        "difficulty": "medium",
        "scenario_id": "medium_07"
    },
    {
        "bug_report": "Concurrent file uploads cause some files to be corrupted or partially written. Sequential uploads work correctly.",
        "ground_truth_type": "race_condition",
        "ground_truth_file": "file_handler.py",
        "ground_truth_fix": "Add file locking mechanism to prevent concurrent writes",
        "repo_modules": ["file_handler.py", "storage.py", "threading.py", "utils.py", "models.py", "api.py", "validation.py", "middleware.py", "config.py", "monitoring.py"],
        "difficulty": "medium",
        "scenario_id": "medium_08"
    },
    {
        "bug_report": "API key validation fails intermittently. The same API key works sometimes and fails other times with 'Invalid API key' error.",
        "ground_truth_type": "authentication",
        "ground_truth_file": "api_auth.py",
        "ground_truth_fix": "Fix API key comparison to use constant-time comparison",
        "repo_modules": ["api_auth.py", "auth.py", "security.py", "utils.py", "models.py", "database.py", "cache.py", "middleware.py", "config.py", "validation.py"],
        "difficulty": "medium",
        "scenario_id": "medium_09"
    },
    {
        "bug_report": "The webhook endpoint fails to process events from external services. The error log shows 'Signature verification failed' for valid requests.",
        "ground_truth_type": "null_pointer",
        "ground_truth_file": "webhook_handler.py",
        "ground_truth_fix": "Fix webhook signature verification to handle different encoding formats",
        "repo_modules": ["webhook_handler.py", "security.py", "crypto.py", "utils.py", "models.py", "api.py", "middleware.py", "config.py", "validation.py", "logging.py"],
        "difficulty": "medium",
        "scenario_id": "medium_10"
    },
    {
        "bug_report": "The export feature generates CSV files with corrupted data. Some fields contain extra characters or are truncated.",
        "ground_truth_type": "logic",
        "ground_truth_file": "csv_exporter.py",
        "ground_truth_fix": "Fix CSV escaping logic to properly handle special characters",
        "repo_modules": ["csv_exporter.py", "data_processor.py", "models.py", "utils.py", "validation.py", "api.py", "database.py", "cache.py", "config.py", "middleware.py"],
        "difficulty": "medium",
        "scenario_id": "medium_11"
    },
    {
        "bug_report": "The background job scheduler fails to execute scheduled tasks. Jobs are created but never run, even after the scheduled time.",
        "ground_truth_type": "logic",
        "ground_truth_file": "job_scheduler.py",
        "ground_truth_fix": "Fix job scheduler to properly check and execute pending jobs",
        "repo_modules": ["job_scheduler.py", "queue.py", "threading.py", "models.py", "utils.py", "database.py", "config.py", "api.py", "middleware.py", "monitoring.py"],
        "difficulty": "medium",
        "scenario_id": "medium_12"
    },
    {
        "bug_report": "The image resizing service produces corrupted images. The output files are smaller than expected and cannot be opened.",
        "ground_truth_type": "performance",
        "ground_truth_file": "image_processor.py",
        "ground_truth_fix": "Fix image processing to properly flush and close file handles",
        "repo_modules": ["image_processor.py", "storage.py", "utils.py", "models.py", "api.py", "middleware.py", "config.py", "validation.py", "cache.py", "monitoring.py"],
        "difficulty": "medium",
        "scenario_id": "medium_13"
    },
    {
        "bug_report": "The email notification service fails silently. Emails are not being sent but no error is logged.",
        "ground_truth_type": "null_pointer",
        "ground_truth_file": "email_service.py",
        "ground_truth_fix": "Add null check for email configuration before attempting to send",
        "repo_modules": ["email_service.py", "config.py", "models.py", "utils.py", "api.py", "middleware.py", "database.py", "cache.py", "validation.py", "logging.py"],
        "difficulty": "medium",
        "scenario_id": "medium_14"
    }
]

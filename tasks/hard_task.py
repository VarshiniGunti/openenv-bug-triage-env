"""Hard task dataset with 14 bug scenarios."""

HARD_SCENARIOS = [
    {
        "bug_report": "The user profile endpoint returns 500 error intermittently. The error occurs only when multiple users request their profiles simultaneously. The logs show 'NullPointerException in profile service' but only under high load.",
        "ground_truth_type": "null_pointer",
        "ground_truth_file": "profile_service.py",
        "ground_truth_fix": "Add null check for user object in profile service before accessing nested properties",
        "repo_modules": ["profile_service.py", "user_service.py", "cache.py", "database.py", "api.py", "middleware.py", "models.py", "utils.py", "validation.py", "config.py", "monitoring.py", "logging.py", "auth.py", "threading.py", "queue.py", "storage.py", "indexing.py", "query.py", "security.py", "metrics.py", "health_check.py"],
        "difficulty": "hard",
        "scenario_id": "hard_01"
    },
    {
        "bug_report": "The analytics dashboard takes 2 minutes to load with 1 year of data but only 5 seconds with 1 month of data. The query appears to be doing full table scans instead of using indexes.",
        "ground_truth_type": "performance",
        "ground_truth_file": "analytics_engine.py",
        "ground_truth_fix": "Add database indexes on timestamp and user_id columns, implement query optimization with pagination",
        "repo_modules": ["analytics_engine.py", "database.py", "query_builder.py", "indexing.py", "cache.py", "models.py", "api.py", "utils.py", "middleware.py", "config.py", "monitoring.py", "logging.py", "aggregation.py", "reporting.py", "storage.py", "validation.py", "security.py", "metrics.py", "auth.py", "threading.py"],
        "difficulty": "hard",
        "scenario_id": "hard_02"
    },
    {
        "bug_report": "Users report being logged out unexpectedly when accessing the application from different geographic locations. The session works fine when staying in one location.",
        "ground_truth_type": "session",
        "ground_truth_file": "session_validator.py",
        "ground_truth_fix": "Remove IP-based session validation that incorrectly invalidates sessions on location change",
        "repo_modules": ["session_validator.py", "session_manager.py", "auth.py", "middleware.py", "security.py", "config.py", "models.py", "utils.py", "database.py", "cache.py", "logging.py", "monitoring.py", "api.py", "validation.py", "geo_service.py", "user_service.py", "token_manager.py", "encryption.py", "metrics.py", "health_check.py"],
        "difficulty": "hard",
        "scenario_id": "hard_03"
    },
    {
        "bug_report": "Memory usage grows by 100MB per day even with no active users. The application reaches 5GB after 50 days. Profiling shows memory is held in the event listener registry.",
        "ground_truth_type": "memory",
        "ground_truth_file": "event_manager.py",
        "ground_truth_fix": "Implement proper event listener cleanup and unsubscribe mechanism",
        "repo_modules": ["event_manager.py", "event_bus.py", "listener_registry.py", "memory_manager.py", "utils.py", "models.py", "database.py", "cache.py", "api.py", "middleware.py", "config.py", "monitoring.py", "logging.py", "threading.py", "queue.py", "storage.py", "metrics.py", "profiler.py", "gc_manager.py", "cleanup.py"],
        "difficulty": "hard",
        "scenario_id": "hard_04"
    },
    {
        "bug_report": "OAuth login fails for users with certain email providers. The error occurs during token validation. The issue appears to be related to how the token signature is verified.",
        "ground_truth_type": "authentication",
        "ground_truth_file": "oauth_validator.py",
        "ground_truth_fix": "Fix JWT token signature verification to handle different key formats correctly",
        "repo_modules": ["oauth_validator.py", "jwt_handler.py", "auth.py", "security.py", "crypto.py", "models.py", "utils.py", "config.py", "database.py", "cache.py", "api.py", "middleware.py", "logging.py", "monitoring.py", "validation.py", "key_manager.py", "token_manager.py", "user_service.py", "metrics.py", "health_check.py"],
        "difficulty": "hard",
        "scenario_id": "hard_05"
    },
    {
        "bug_report": "The recommendation engine produces inconsistent results. The same user gets different recommendations on different days. The algorithm uses weighted scoring but the weights appear to be applied incorrectly.",
        "ground_truth_type": "logic",
        "ground_truth_file": "recommendation_engine.py",
        "ground_truth_fix": "Fix weight normalization in recommendation scoring algorithm",
        "repo_modules": ["recommendation_engine.py", "scoring.py", "ml_model.py", "feature_extractor.py", "database.py", "cache.py", "models.py", "utils.py", "api.py", "middleware.py", "config.py", "monitoring.py", "logging.py", "validation.py", "data_processor.py", "indexing.py", "query.py", "metrics.py", "profiler.py", "storage.py"],
        "difficulty": "hard",
        "scenario_id": "hard_06"
    },
    {
        "bug_report": "Database replication fails intermittently. The primary database works but replicas fall out of sync. The error logs show 'Connection timeout' during replication sync.",
        "ground_truth_type": "database",
        "ground_truth_file": "replication_manager.py",
        "ground_truth_fix": "Increase replication timeout and implement retry logic with exponential backoff",
        "repo_modules": ["replication_manager.py", "database.py", "connection_pool.py", "sync_engine.py", "models.py", "utils.py", "config.py", "monitoring.py", "logging.py", "api.py", "middleware.py", "health_check.py", "metrics.py", "query.py", "transaction_manager.py", "backup.py", "recovery.py", "validation.py", "security.py", "threading.py"],
        "difficulty": "hard",
        "scenario_id": "hard_07"
    },
    {
        "bug_report": "Data corruption occurs when multiple services write to the same database table simultaneously. The corruption manifests as duplicate records or missing fields.",
        "ground_truth_type": "race_condition",
        "ground_truth_file": "transaction_manager.py",
        "ground_truth_fix": "Implement proper transaction isolation levels and row-level locking",
        "repo_modules": ["transaction_manager.py", "database.py", "lock_manager.py", "models.py", "query.py", "utils.py", "config.py", "monitoring.py", "logging.py", "api.py", "middleware.py", "validation.py", "threading.py", "queue.py", "metrics.py", "profiler.py", "recovery.py", "backup.py", "replication_manager.py", "health_check.py"],
        "difficulty": "hard",
        "scenario_id": "hard_08"
    },
    {
        "bug_report": "API rate limiting fails to prevent abuse. Some users can make unlimited requests while others are blocked. The rate limit counter appears to be shared incorrectly across requests.",
        "ground_truth_type": "authentication",
        "ground_truth_file": "rate_limiter.py",
        "ground_truth_fix": "Fix rate limit counter to use per-user tracking with proper cache invalidation",
        "repo_modules": ["rate_limiter.py", "auth.py", "cache.py", "models.py", "utils.py", "config.py", "middleware.py", "api.py", "database.py", "monitoring.py", "logging.py", "metrics.py", "security.py", "validation.py", "user_service.py", "token_manager.py", "threading.py", "queue.py", "storage.py", "health_check.py"],
        "difficulty": "hard",
        "scenario_id": "hard_09"
    },
    {
        "bug_report": "The distributed cache becomes inconsistent across nodes. Some nodes have stale data while others have fresh data. The cache invalidation mechanism appears to be broken.",
        "ground_truth_type": "race_condition",
        "ground_truth_file": "distributed_cache.py",
        "ground_truth_fix": "Implement proper cache invalidation with distributed locking and message broadcasting",
        "repo_modules": ["distributed_cache.py", "cache.py", "lock_manager.py", "messaging.py", "models.py", "utils.py", "config.py", "monitoring.py", "logging.py", "api.py", "middleware.py", "validation.py", "threading.py", "queue.py", "metrics.py", "profiler.py", "storage.py", "health_check.py"],
        "difficulty": "hard",
        "scenario_id": "hard_10"
    },
    {
        "bug_report": "The machine learning model inference service crashes under high load. The error shows 'Out of memory' even though the server has sufficient RAM.",
        "ground_truth_type": "memory",
        "ground_truth_file": "ml_inference.py",
        "ground_truth_fix": "Implement batch processing with memory pooling and garbage collection optimization",
        "repo_modules": ["ml_inference.py", "model_loader.py", "memory_manager.py", "utils.py", "models.py", "api.py", "middleware.py", "config.py", "monitoring.py", "logging.py", "metrics.py", "profiler.py", "threading.py", "queue.py", "storage.py", "health_check.py", "gc_manager.py", "cleanup.py", "validation.py"],
        "difficulty": "hard",
        "scenario_id": "hard_11"
    },
    {
        "bug_report": "The microservices communication fails intermittently with 'Service unavailable' errors. The services are running but requests timeout randomly.",
        "ground_truth_type": "performance",
        "ground_truth_file": "service_mesh.py",
        "ground_truth_fix": "Implement circuit breaker pattern with exponential backoff and connection pooling",
        "repo_modules": ["service_mesh.py", "api_client.py", "connection_pool.py", "retry_logic.py", "models.py", "utils.py", "config.py", "monitoring.py", "logging.py", "middleware.py", "metrics.py", "health_check.py", "threading.py", "queue.py", "validation.py", "security.py", "auth.py", "storage.py", "profiler.py"],
        "difficulty": "hard",
        "scenario_id": "hard_12"
    },
    {
        "bug_report": "The data pipeline produces inconsistent results when processing the same input data. The output varies depending on the order of processing steps.",
        "ground_truth_type": "logic",
        "ground_truth_file": "data_pipeline.py",
        "ground_truth_fix": "Fix data transformation logic to ensure deterministic processing order and proper state management",
        "repo_modules": ["data_pipeline.py", "data_processor.py", "transformation.py", "models.py", "utils.py", "database.py", "cache.py", "api.py", "middleware.py", "config.py", "monitoring.py", "logging.py", "validation.py", "metrics.py", "profiler.py", "storage.py", "threading.py", "queue.py"],
        "difficulty": "hard",
        "scenario_id": "hard_13"
    },
    {
        "bug_report": "The backup and recovery system fails to restore data correctly. Restored data is missing recent changes or contains corrupted records.",
        "ground_truth_type": "database",
        "ground_truth_file": "backup_manager.py",
        "ground_truth_fix": "Fix backup snapshot consistency and implement proper transaction log replay",
        "repo_modules": ["backup_manager.py", "database.py", "transaction_manager.py", "recovery.py", "replication_manager.py", "models.py", "utils.py", "config.py", "monitoring.py", "logging.py", "api.py", "middleware.py", "validation.py", "metrics.py", "storage.py", "health_check.py", "threading.py", "queue.py", "security.py"],
        "difficulty": "hard",
        "scenario_id": "hard_14"
    }
]

"""
Constants for background workers.

All worker-related constants are centralized here to avoid duplication
and make configuration changes easier.
"""

# ===== FOLDER NAMES =====
# Common folder for worker data (runs, executions, etc.)
DATA_FOLDER = "data"

# Folder where generated reports are stored (HTML, JSON, Word, PDF)
REPORTS_FOLDER = "reports"

# ===== FILE NAMES =====
# Discovery worker data file
DISCOVERY_DATA_FILE = "discovery_data.json"

# Common execution log file for all workers
EXECUTION_LOG_FILE = "worker_executions.json"

# Sync worker data file
DATABASE_SYNC_DATA_FILE = "sync_data.json"

# ===== TIMEOUTS & INTERVALS =====
# Discovery worker safety margin for lookback (minutes)
DISCOVERY_SAFETY_MARGIN_MINUTES = 15

# Discovery worker first run lookback period (hours)
DISCOVERY_FIRST_RUN_LOOKBACK_HOURS = 480

# Base worker timeout for considering runs failed (minutes)
WORKER_RUN_TIMEOUT_MINUTES = 60

# Summary worker timeout for stuck processing (hours)
SUMMARY_PROCESSING_TIMEOUT_HOURS = 1

# Sync worker timeout for considering runs failed (hours)
DATABASE_SYNC_WORKER_TIMEOUT_HOURS = 2

# Maximum retry attempts for failed laws before giving up
MAX_LAW_RETRY_ATTEMPTS = 3

# ===== DISPATCHER TIMING =====
# Discovery loop interval (seconds)
DISCOVERY_LOOP_INTERVAL_SECONDS = 60 * 60

# Processing loop interval (seconds)
PROCESSING_LOOP_INTERVAL_SECONDS = 3 * 60

# Database sync scheduled time (UTC hour)
DATABASE_SYNC_SCHEDULED_HOUR_UTC = 3

# Evaluation metrics snapshot scheduled time (UTC hour)
EVALUATION_SNAPSHOT_SCHEDULED_HOUR_UTC = 2

# Error retry wait time (seconds)
ERROR_RETRY_WAIT_SECONDS = 5 * 60
ERROR_RETRY_WAIT_SHORT_SECONDS = 60

# ===== RECONCILIATION WORKER =====
# Reconciliation loop interval (hours)
RECONCILIATION_INTERVAL_HOURS = 12

# Safety margin for reconciliation lookback (hours)
RECONCILIATION_SAFETY_MARGIN_HOURS = 1

# Reconciliation worker first run lookback period (hours)
RECONCILIATION_FIRST_RUN_LOOKBACK_HOURS = 24

# Maximum time window for reconciliation queries (days) to prevent overwhelming EUR-Lex
RECONCILIATION_MAX_TIME_WINDOW_DAYS = 30

# Reconciliation data tracking file
RECONCILIATION_DATA_FILE = "reconciliation_data.json"

# Missing acts log file
MISSING_ACTS_LOG_FILE = "missing_acts_log.json"

# Maximum age for acts in raw folder before considered stuck (hours)
RAW_ACT_MAX_AGE_HOURS = 24

# ===== EUROVOC BACKFILL (RECONCILIATION) =====
# - "window": scan only last EUROVOC_BACKFILL_LOOKBACK_DAYS days
# - "all": scan all laws in DB up to EUROVOC_BACKFILL_MAX_LAWS
EUROVOC_BACKFILL_MODE = "window"
# How many days back to backfill EuroVoc labels (past couple of days)
EUROVOC_BACKFILL_LOOKBACK_DAYS = 4
EUROVOC_BACKFILL_MAX_LAWS = 500

# ===== DATABASE SYNC WORKER CONSTANTS =====
# Batch size for processing sync operations (smaller for nice behavior)
SYNC_BATCH_SIZE = 25

# Delay between sync batches to keep the database reactive
SYNC_BATCH_DELAY_SECONDS = 1

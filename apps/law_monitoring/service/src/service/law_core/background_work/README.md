# Worker Constants Usage Documentation

> **⚠️ IMPORTANT**: This documentation should be updated every time the usage of worker constants is modified, added, or removed from the codebase. Please keep this file in sync with the actual usage patterns in `workers_constants.py`.

This document provides a comprehensive overview of where each constant from `workers_constants.py` is used throughout the law monitoring system's codebase.

## Overview

The `workers_constants.py` file centralizes all worker-related constants to avoid duplication and make configuration changes easier. These constants control folder names, file names, timeouts, intervals, and other configuration parameters used by the background worker system.

## Constants Usage Summary

### **FOLDER NAMES**

#### `DATA_FOLDER` ("data")
- **Used in 6 files**
- **Purpose**: Common folder for worker data (runs, executions, etc.)
- **Usage locations**:
  - `discovery_worker.py`: Loading/saving discovery data file
  - `reconciliation_worker.py`: Storing reconciliation data and missing acts log
  - `base_worker.py`: Creating folder structure, execution logs, and runs tracking
  - `database_sync_worker.py`: Loading/saving sync data
  - `sqlite_file_cache_exclusion_policy.py`: Cache exclusion rules

#### `RAW_LAWS_FOLDER` ("raw_law_data")
- **Used in 6 files**
- **Purpose**: Storage for newly discovered laws awaiting processing
- **Usage locations**:
  - `discovery_worker.py`: Saving discovered laws, checking for duplicates
  - `summary_worker.py`: Reading laws for processing, moving to processed/failed
  - `reconciliation_worker.py`: Validating existing raw acts
  - `law_data_service.py`: Loading laws for API endpoints
  - `metrics.py`: Counting raw files for system metrics

#### `PROCESSED_LAWS_FOLDER` ("processed_law_data")
- **Used in 6 files**
- **Purpose**: Storage for successfully processed laws
- **Usage locations**:
  - `summary_worker.py`: Moving successfully processed laws from raw folder
  - `reconciliation_worker.py`: Checking for already processed acts
  - `law_data_service.py`: Loading processed laws for API access
  - `metrics.py`: Counting processed files
  - `discovery_worker.py`: Checking for duplicates

#### `FAILED_LAWS_FOLDER` ("failed_law_data")
- **Used in 6 files**
- **Purpose**: Storage for laws that failed processing after max retries
- **Usage locations**:
  - `summary_worker.py`: Moving failed laws after max retry attempts
  - `reconciliation_worker.py`: Checking for acts that previously failed
  - `law_data_service.py`: Loading failed laws for analysis
  - `metrics.py`: Counting failed files
  - `discovery_worker.py`: Checking for duplicates

#### `REPORTS_FOLDER` ("reports")
- **Used in 3 files**
- **Purpose**: Storage for generated reports (HTML, JSON, Word, PDF)
- **Usage locations**:
  - `summary_agent.py`: Saving generated reports in multiple formats
  - `routes.py`: Loading reports for API delivery
  - `reconciliation_worker.py`: Checking for existing report files

### **FILE NAMES**

#### `DISCOVERY_DATA_FILE` ("discovery_data.json")
- **Used in 1 file**: `discovery_worker.py`
- **Purpose**: Tracking discovery worker state and last run timestamp

#### `EXECUTION_LOG_FILE` ("worker_executions.json")
- **Used in 1 file**: `base_worker.py`
- **Purpose**: Logging all worker execution events across the system

#### `DATABASE_SYNC_DATA_FILE` ("sync_data.json")
- **Used in 1 file**: `database_sync_worker.py`
- **Purpose**: Tracking database synchronization state

#### `RECONCILIATION_DATA_FILE` ("reconciliation_data.json")
- **Used in 1 file**: `reconciliation_worker.py`
- **Purpose**: Tracking reconciliation worker state and progress

#### `MISSING_ACTS_LOG_FILE` ("missing_acts_log.json")
- **Used in 1 file**: `reconciliation_worker.py`
- **Purpose**: Logging acts that were discovered but are missing from local storage

### **TIMEOUTS & INTERVALS**

#### `DISCOVERY_SAFETY_MARGIN_MINUTES` (15)
- **Used in 1 file**: `discovery_worker.py`
- **Purpose**: Safety buffer when calculating discovery start date to avoid missing laws

#### `DISCOVERY_FIRST_RUN_LOOKBACK_HOURS` (480 = 20 days)
- **Used in 1 file**: `discovery_worker.py`
- **Purpose**: How far back to look on first discovery run to catch historical laws

#### `WORKER_RUN_TIMEOUT_MINUTES` (60)
- **Used in 1 file**: `base_worker.py`
- **Purpose**: Base timeout for considering worker runs as failed

#### `SUMMARY_PROCESSING_TIMEOUT_HOURS` (1)
- **Used in 1 file**: `summary_worker.py`
- **Purpose**: Timeout for detecting stuck law processing operations

#### `DATABASE_SYNC_WORKER_TIMEOUT_HOURS` (2)
- **Used in 1 file**: `database_sync_worker.py`
- **Purpose**: Specific timeout for database sync operations (converted to minutes)

#### `MAX_LAW_RETRY_ATTEMPTS` (3)
- **Used in 1 file**: `summary_worker.py`
- **Purpose**: Maximum retry attempts before moving law to failed folder

### **DISPATCHER TIMING**

#### `DISCOVERY_LOOP_INTERVAL_SECONDS` (3600 = 1 hour)
- **Used in 1 file**: `background_dispatchers.py`
- **Purpose**: How often the discovery loop runs to find new laws

#### `PROCESSING_LOOP_INTERVAL_SECONDS` (180 = 3 minutes)
- **Used in 1 file**: `background_dispatchers.py`
- **Purpose**: How often the processing loop runs to handle discovered laws

#### `DATABASE_SYNC_SCHEDULED_HOUR_UTC` (3)
- **Used in 1 file**: `background_dispatchers.py`
- **Purpose**: UTC hour when daily database sync is scheduled (3 AM UTC)

#### `ERROR_RETRY_WAIT_SECONDS` (300 = 5 minutes)
- **Used in 1 file**: `background_dispatchers.py`
- **Purpose**: Wait time after errors in discovery and database sync loops

#### `ERROR_RETRY_WAIT_SHORT_SECONDS` (60)
- **Used in 1 file**: `background_dispatchers.py`
- **Purpose**: Shorter wait time after errors in processing loop

### **RECONCILIATION WORKER**

#### `RECONCILIATION_INTERVAL_HOURS` (12)
- **Used in 1 file**: `background_dispatchers.py`
- **Purpose**: How often reconciliation runs to check for missing acts

#### `RECONCILIATION_SAFETY_MARGIN_HOURS` (1)
- **Used in 1 file**: `reconciliation_worker.py`
- **Purpose**: Safety buffer when calculating reconciliation time windows

#### `RECONCILIATION_FIRST_RUN_LOOKBACK_HOURS` (24)
- **Used in 1 file**: `reconciliation_worker.py`
- **Purpose**: How far back to look on first reconciliation run

#### `RECONCILIATION_MAX_TIME_WINDOW_DAYS` (30)
- **Used in 1 file**: `reconciliation_worker.py`
- **Purpose**: Maximum time window to prevent overwhelming EUR-Lex API

#### `RAW_ACT_MAX_AGE_HOURS` (24)
- **Used in 1 file**: `reconciliation_worker.py`
- **Purpose**: Threshold for considering raw acts as "stuck" in processing

### **DATABASE SYNC WORKER**

#### `SYNC_BATCH_SIZE` (25)
- **Used in 1 file**: `sqlite_file_cache_synchronizer.py`
- **Purpose**: Batch size for database sync operations to maintain system responsiveness

#### `SYNC_BATCH_DELAY_SECONDS` (1)
- **Used in 1 file**: `sqlite_file_cache_synchronizer.py`
- **Purpose**: Delay between sync batches to keep database reactive

## File Usage Summary

### Most Used Constants
- **6 files**: `DATA_FOLDER`, `RAW_LAWS_FOLDER`, `PROCESSED_LAWS_FOLDER`, `FAILED_LAWS_FOLDER`
- **3 files**: `REPORTS_FOLDER`

### Worker-Specific Files
- **Discovery Worker**: Uses 5 constants for timing, safety margins, and data persistence
- **Summary Worker**: Uses 6 constants for timeouts, retries, and folder management
- **Reconciliation Worker**: Uses 12 constants (most extensive usage) for timing, validation, and data tracking
- **Database Sync Worker**: Uses 4 constants for timeouts and batch processing
- **Background Dispatchers**: Uses 7 constants for loop timing and error handling

## System Architecture Impact

The constants are well-centralized and each serves a specific purpose in the law monitoring system's background worker architecture. They control:

1. **File Organization**: Proper separation of raw, processed, failed, and report data
2. **Timing Control**: Regular intervals for discovery, processing, and reconciliation
3. **Error Handling**: Timeouts, retries, and recovery mechanisms
4. **Performance Tuning**: Batch sizes and delays to maintain system responsiveness
5. **Data Integrity**: Safety margins and validation thresholds

## Maintenance Guidelines

When modifying constants usage:

1. Update the constant value in `workers_constants.py`
2. Test all affected components listed in this documentation
3. Update this README.md file with any new usage patterns
4. Consider backward compatibility for persistent data files
5. Update any related configuration documentation

## Last Updated

This documentation was last updated based on the codebase state as of the current commit. Please verify usage patterns when making changes to ensure accuracy. 
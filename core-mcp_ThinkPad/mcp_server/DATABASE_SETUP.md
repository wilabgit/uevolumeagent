# Database Storage Setup Guide

This guide explains how to set up PostgreSQL-based persistent storage for the callback-mcp-server instead of using in-memory storage.

## Overview

The callback-mcp-server now supports two storage backends:

1. **Memory** (default): In-memory storage with configurable capacity
2. **PostgreSQL**: Persistent database storage with SQL querying capabilities

## Prerequisites

- PostgreSQL 12+ installed and running
- Python 3.10+
- Dependencies: `sqlalchemy`, `psycopg2-binary`

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Using pip
pip install sqlalchemy psycopg2-binary

# Or using uv (if configured)
uv pip install sqlalchemy psycopg2-binary
```

### Step 2: Configure PostgreSQL Connection

Create a `.env` file in the callback-mcp-server directory:

```bash
# Copy the example
cp .env.example .env

# Edit with your PostgreSQL credentials
# Default values:
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_NAME=callback_server
```

### Step 3: Create the Database

The provided `setup_db.py` script handles database creation:

```bash
# Full setup (create database + init tables)
python setup_db.py --full-setup

# Or step by step:
python setup_db.py --create-db      # Create the PostgreSQL database
python setup_db.py --migrate        # Initialize tables in existing database
```

### Step 4: Activate PostgreSQL Storage

In your `.env` file, set:

```bash
STORAGE_TYPE=postgresql
```

### Step 5: Start the Server

```bash
python startServer.py
```

## Database Schema

The `event_reports` table stores all event notifications with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key, auto-incremented |
| `supi` | VARCHAR(255) | Subscriber identifier (indexed) |
| `notif_id` | VARCHAR(255) | Notification ID |
| `event` | VARCHAR(128) | Event type |
| `timestamp` | TIMESTAMP | Event timestamp (indexed) |
| `received_at` | TIMESTAMP | Server receive timestamp |
| `event_data` | JSON | Full event data as JSON |
| `raw_json` | TEXT | Raw JSON string |

**Indexes** for performance:
- `idx_supi_timestamp`: Optimizes queries by SUPI + timestamp
- `idx_notif_id`: Optimizes queries by notification ID
- Default index on SUPI

## API Methods (Identical Interface)

All data store methods work identically whether using memory or PostgreSQL:

```python
from data_store import data_store

# Add a report
data_store.add_report(event_notification)

# Get reports for a specific UE
reports = data_store.get_ue_reports("some_supi")

# Get all reports (with pagination in DB version)
all_reports = data_store.get_all_reports()

# Get list of unique UEs
ues = data_store.get_ue_list()

# Get statistics
stats = data_store.get_statistics()

# Clear all data
data_store.clear()
```

## Additional Database Features

The DatabaseStore class provides additional methods:

```python
# Get reports for a specific event type
event_reports = data_store.get_reports_for_event("USAGE_REPORT", limit=100)

# Check database health
is_healthy = data_store.health_check()
```

## Performance Characteristics

### In-Memory Storage
- **Pros**: Fast access, no external dependencies
- **Cons**: Data lost on restart, limited capacity
- **Best for**: Development, testing, small deployments

### PostgreSQL Storage
- **Pros**: Persistent, queryable, scalable, backup-friendly
- **Cons**: Slightly higher latency, requires PostgreSQL instance
- **Best for**: Production, data persistence, long-term archival

## Troubleshooting

### Database Connection Failed

**Error**: `postgresql://user:pass@localhost/callback_server (Connection refused)`

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   psql --version
   sudo service postgresql status
   ```

2. Check connection parameters in `.env`:
   ```bash
   psql -h localhost -p 5432 -U postgres
   ```

3. Create database manually:
   ```bash
   createdb -h localhost -U postgres callback_server
   ```

### Permission Denied

**Error**: `FATAL: Ident authentication failed for user "postgres"`

**Solution**: Update PostgreSQL authentication method or use:
```bash
psql -h localhost -U postgres --password
```

### Table Already Exists

This is safe - tables are only created if they don't exist.

## Migration: Memory to PostgreSQL

To migrate from in-memory to PostgreSQL without data loss:

1. Set `STORAGE_TYPE=memory` and collect all data:
   ```python
   from data_store import data_store
   all_reports = data_store.get_all_reports()
   ```

2. Switch to PostgreSQL:
   - Update `.env` with `STORAGE_TYPE=postgresql`
   - Run `python setup_db.py --full-setup`

3. Re-import data:
   ```python
   for report in all_reports:
       data_store.add_report(report)
   ```

## Monitoring and Queries

Connect directly to PostgreSQL for analysis:

```bash
psql -h localhost -U postgres -d callback_server

# List all tables
\dt

# Count reports
SELECT COUNT(*) FROM event_reports;

# View reports by SUPI
SELECT * FROM event_reports WHERE supi = 'your_supi' ORDER BY timestamp;

# Daily report count
SELECT DATE(received_at), COUNT(*) FROM event_reports GROUP BY DATE(received_at);
```

## Advanced Configuration

### Enable SQL Query Logging

```bash
DB_ECHO=True
```

This logs all SQL queries to help with debugging.

### Connection Pool Settings

Edit `database.py` to customize connection pooling:

```python
self.engine = create_engine(
    database_url,
    pool_size=20,           # Number of connections to maintain
    max_overflow=40,        # Maximum overflow connections
    pool_pre_ping=True      # Test connections before use
)
```

## Performance Optimization

For high-volume deployments (> 100 reports/second):

1. **Increase batch commit size** (periodic commits instead of per-report)
2. **Add database replication** for read-heavy workloads
3. **Implement table partitioning** by date for large datasets
4. **Add cleanup job** to archive old reports

Contact your database administrator for production deployment.

# PostgreSQL Storage Implementation - Quick Start

## What Was Changed

Your callback-mcp-server now supports persistent PostgreSQL storage alongside the existing in-memory storage. Here's what's new:

### Files Added
- **`database.py`** - PostgreSQL models and database interface using SQLAlchemy
- **`setup_db.py`** - Database initialization and setup script
- **`DATABASE_SETUP.md`** - Comprehensive setup documentation

### Files Modified
- **`config.py`** - Added PostgreSQL configuration parameters
- **`data_store.py`** - Added factory function to choose between memory and database backends
- **`pyproject.toml`** - Added dependencies: `sqlalchemy`, `psycopg2-binary`, `alembic`
- **`.env.example`** - Added database configuration examples

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install sqlalchemy psycopg2-binary
```

### 2. Configure Database Connection
Create/update `.env` file:
```bash
STORAGE_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=callback_server
```

### 3. Initialize Database
```bash
python setup_db.py --full-setup
```

### 4. Start Server
```bash
python startServer.py
```

That's it! Your reports are now stored in PostgreSQL.

## Key Features

✅ **Same API** - No code changes needed, works with existing code  
✅ **Persistent Storage** - Reports survive server restart  
✅ **Query Support** - Full SQL queries for analytics  
✅ **Indexed** - Fast lookups by SUPI, timestamp, notification ID  
✅ **Scalable** - Handles thousands of reports  
✅ **Fallback** - Automatically falls back to memory if DB unavailable  
✅ **Easy Migration** - Switch between storage types with env variable  

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_TYPE` | `postgresql` | `memory` or `postgresql` |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `DB_NAME` | `callback_server` | Database name |
| `DB_ECHO` | `False` | Log SQL queries |
| `MAX_REPORTS` | `10000` | Max reports (memory mode only) |

## Usage Examples

All existing code continues to work:

```python
from data_store import data_store

# Add a report (automatically goes to PostgreSQL)
data_store.add_report(event_notif)

# Get reports for UE
reports = data_store.get_ue_reports("some_supi")

# Get all reports
all_reports = data_store.get_all_reports()

# Get statistics
stats = data_store.get_statistics()
```

New database-specific methods:

```python
# Query by event type
usage_reports = data_store.get_reports_for_event("USAGE_REPORT")

# Check database health
if data_store.health_check():
    print("Database is healthy")
```

## Database Schema

Single table `event_reports`:
- `id` - Primary key
- `supi` - User identifier (indexed)
- `notif_id` - Notification ID
- `event` - Event type
- `timestamp` - Event timestamp (indexed)
- `received_at` - Server receive time
- `event_data` - Full JSON data
- `raw_json` - Raw JSON string

## Troubleshooting

**"Connection refused"?**
- Make sure PostgreSQL is running
- Check connection details in `.env`

**"FATAL: database XXX does not exist"?**
- Run: `python setup_db.py --full-setup`

**Want to switch back to memory storage?**
- Set `STORAGE_TYPE=memory` in `.env`

## Next Steps

1. See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed documentation
2. Connect to database for direct queries: `psql callback_server`
3. Set up automated backups of your PostgreSQL database
4. Consider adding an index cleanup job for production

For Kafka integration in the future, let me know!

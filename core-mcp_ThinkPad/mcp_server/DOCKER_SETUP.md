# Database Setup with Docker Compose

If you don't have PostgreSQL installed locally, you can use Docker Compose to run PostgreSQL in a container.

## Prerequisites

- Docker and Docker Compose installed
- About 200MB disk space for the PostgreSQL image

## Quick Start

### 1. Start PostgreSQL Container

```bash
# Start PostgreSQL in background
docker-compose up -d

# Verify it's running
docker-compose ps
```

You should see:
```
NAME                              STATUS
callback-server-postgres          Up X seconds (healthy)
```

### 2. Configure Your Application

Create/update `.env` file with:

```bash
STORAGE_TYPE=postgresql
DB_HOST=localhost          # Works because Docker maps port 5432
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=callback_server
```

### 3. Initialize Database Tables

```bash
python setup_db.py --full-setup
```

### 4. Run Tests

```bash
python test_database.py
```

## Docker Compose Commands

```bash
# Start PostgreSQL (background)
docker-compose up -d

# Check logs
docker-compose logs postgres

# Stop PostgreSQL
docker-compose stop

# Remove containers (keeps data volume)
docker-compose down

# Remove containers AND data (full cleanup)
docker-compose down -v

# Connect to PostgreSQL directly
docker-compose exec postgres psql -U postgres -d callback_server
```

## Accessing the Database

### From Host Machine

```bash
# Connect with psql (if installed)
psql -h localhost -U postgres -d callback_server

# Or use the Docker container:
docker-compose exec postgres psql -U postgres -d callback_server
```

### Useful SQL Queries

```sql
-- Count all reports
SELECT COUNT(*) FROM event_reports;

-- View recent reports
SELECT supi, event, received_at FROM event_reports 
ORDER BY received_at DESC LIMIT 10;

-- Reports per UE
SELECT supi, COUNT(*) FROM event_reports 
GROUP BY supi ORDER BY COUNT(*) DESC;

-- Daily report counts
SELECT DATE(received_at), COUNT(*) FROM event_reports 
GROUP BY DATE(received_at) ORDER BY DATE(received_at) DESC;
```

## Backing Up the Database

```bash
# Backup to file
docker-compose exec postgres pg_dump -U postgres callback_server > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres callback_server < backup.sql
```

## Troubleshooting

### Port Already in Use

If port 5432 is already in use:

```bash
# Edit docker-compose.yml and change:
ports:
  - "5433:5432"  # Maps container port to 5433

# Then update .env:
DB_PORT=5433
```

### Container Won't Start

```bash
# Check logs
docker-compose logs postgres

# Rebuild image
docker-compose down -v
docker-compose up --build
```

### Can't Connect to Database

1. Verify container is running: `docker-compose ps`
2. Check logs: `docker-compose logs postgres`
3. Ensure firewall allows port 5432
4. Try connecting directly: `docker-compose exec postgres psql -U postgres`

## Cleanup

To completely remove the PostgreSQL container and data:

```bash
docker-compose down -v
```

This removes:
- Container
- Volume (database data)
- Network

To preserve data when stopping:

```bash
docker-compose stop  # Keeps everything
docker-compose start # Restart later
```

## Production Note

For production deployments, don't use Docker containers. Instead:
1. Use managed PostgreSQL (AWS RDS, Azure Database, DigitalOcean, etc.)
2. Set connection details in `.env` file
3. Configure proper backups and replication
4. Use strong passwords and network security

Docker Compose is excellent for:
- Development
- Testing
- Local demos
- CI/CD pipelines

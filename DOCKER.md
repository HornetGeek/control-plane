# Docker Setup for Control Plane API

This document describes how to use Docker to run the Control Plane API and its dependencies.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Start all services

```bash
# Using docker-compose directly
docker-compose up -d

# Or using make
make up-detach
```

This will start:
- **PostgreSQL** on port 5432
- **Zitadel** (OIDC Provider) on ports 8080 (HTTP) and 9090 (Console)
- **Control Plane API** on port 8000

### 2. Run database migrations

```bash
# Using docker-compose with profile
docker-compose --profile migrate up migrate

# Or using make
make migrate
```

### 3. Check service health

```bash
# API Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready
```

### 4. View logs

```bash
# All services
docker-compose logs -f

# API only
make logs-api

# Database only
make logs-db
```

## Services

### PostgreSQL Database
- **Host**: localhost:5432
- **Database**: control_plane
- **Username**: control_plane
- **Password**: control_plane_password
- **Data**: Persisted in Docker volume `postgres_data`

Connect directly:
```bash
docker-compose exec postgres psql -U control_plane -d control_plane
```

### Zitadel (OIDC Identity Provider)
- **Console**: http://localhost.zitadel.127.0.0.1.sslip.io:9090
- **Issuer URL**: http://localhost.zitadel.127.0.0.1.sslip.io:8080/default
- **Admin User**: admin@zitadel.localhost.zitadel.127.0.0.1.sslip.io
- **Admin Password**: adminAdmin!

To configure Zitadel for your application:
1. Log in to the console
2. Create a new project
3. Create an OIDC application (Web Application)
4. Set redirect URIs to: `http://localhost:8000/v1/auth/callback`
5. Add custom claim `org_id` to the token
6. Copy client ID and secret to `.env` file

### Control Plane API
- **API Base URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

## Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

For Docker Compose with local Zitadel, update these values:

```bash
# .env file
OIDC_ISSUER=http://localhost.zitadel.127.0.0.1.sslip.io:8080/default
OIDC_CLIENT_ID=your-client-id-from-zitadel
OIDC_CLIENT_SECRET=your-client-secret-from-zitadel
DATABASE_URL=postgresql+asyncpg://control_plane:control_plane_password@postgres:5432/control_plane
```

## Development Workflow

### Hot Reload (Development)

For auto-reload on code changes, use the override file:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
docker-compose up
```

### Running Tests

```bash
# Run tests in container
docker-compose exec api pytest -v

# Run with coverage
docker-compose exec api pytest --cov=src --cov-report=html
```

### Database Shell

```bash
# PostgreSQL shell
make shell-db

# Or using docker-compose directly
docker-compose exec postgres psql -U control_plane -d control_plane
```

### API Shell

```bash
# Shell inside API container
make shell

# Or using docker-compose directly
docker-compose exec api sh
```

## Make Commands

The Makefile provides convenient shortcuts:

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make build` | Build Docker images |
| `make up` | Start services in foreground |
| `make up-detach` | Start services in background |
| `make down` | Stop services |
| `make down-volumes` | Stop services and remove volumes |
| `make logs` | Show logs from all services |
| `make logs-api` | Show API logs |
| `make logs-db` | Show database logs |
| `make shell` | Open shell in API container |
| `make shell-db` | Open psql shell |
| `make migrate` | Run database migrations |
| `make test` | Run tests |
| `make rebuild` | Rebuild and restart services |
| `make clean` | Remove all containers, images, and volumes |
| `make ps` | Show running containers |

## Production Considerations

For production deployment:

1. **Use specific image tags** instead of `latest`
2. **Set proper secrets** for database and OIDC
3. **Enable HTTPS** for all services
4. **Use external database** (managed PostgreSQL)
5. **Use external OIDC provider** (production Zitadel instance)
6. **Configure resource limits** in docker-compose.yml
7. **Set up monitoring** and logging aggregation
8. **Run behind a reverse proxy** (nginx/traefik)

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs api
```

### Database connection errors

Ensure database is healthy:
```bash
docker-compose ps
```

### Zitadel connection errors

Zitadel takes time to initialize on first start. Wait 30-60 seconds after first run.

### Clean restart

Remove all containers and volumes:
```bash
make down-volumes
make build
make up-detach
```

## Stopping Services

```bash
# Stop containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers with volumes
docker-compose down -v
```

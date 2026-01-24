# md2office - Docker Deployment Guide

**Version 0.1.0**

This guide covers deploying md2office using Docker and Docker Compose for both production and development environments.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Variables](#environment-variables)
3. [Volume Mounts](#volume-mounts)
4. [Production vs Development](#production-vs-development)
5. [Health Checks](#health-checks)
6. [Resource Limits](#resource-limits)
7. [Advanced Configuration](#advanced-configuration)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Production deployment
docker-compose up -d

# Development with hot reload
docker-compose --profile dev up md2office-dev

# Stop services
docker-compose down
```

### Using Docker

```bash
# Build the image
docker build -t md2office:latest .

# Run production container
docker run -d \
  --name md2office \
  -p 8080:8080 \
  -v $(pwd)/templates:/app/templates:ro \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/output:/app/output \
  -e MD2OFFICE_HOST=0.0.0.0 \
  -e MD2OFFICE_PORT=8080 \
  -e MD2OFFICE_LOG_LEVEL=info \
  md2office:latest

# View logs
docker logs -f md2office

# Stop container
docker stop md2office
```

### Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8080/health

# Test conversion
curl -X POST http://localhost:8080/api/v1/convert \
  -F "file=@test.md" \
  -F "template=professional" \
  -o output.docx
```

## Environment Variables

md2office supports configuration through environment variables, which override settings in `config/config.yaml`.

### Complete Reference

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `MD2OFFICE_HOST` | Server bind address | `0.0.0.0` | No | `127.0.0.1` |
| `MD2OFFICE_PORT` | Server port | `8080` | No | `9000` |
| `MD2OFFICE_LOG_LEVEL` | Logging level | `info` | No | `debug`, `info`, `warning`, `error` |
| `MD2OFFICE_WORKERS` | Number of worker processes | `1` | No | `4` |
| `MD2OFFICE_RELOAD` | Enable auto-reload | `false` | No | `true` (dev only) |
| `MD2OFFICE_TEMPLATES_DIR` | Templates directory path | `templates` | No | `/data/templates` |
| `MD2OFFICE_OUTPUT_DIR` | Output directory path | `output` | No | `/data/output` |
| `MD2OFFICE_TEMP_DIR` | Temporary files directory | `temp` | No | `/tmp/md2office` |
| `MD2OFFICE_MAX_FILE_SIZE` | Maximum upload size (bytes) | `10485760` | No | `52428800` (50MB) |
| `MD2OFFICE_DEFAULT_TEMPLATE` | Default template name | `default` | No | `professional` |

### Setting Environment Variables

**Docker Compose:**

```yaml
services:
  md2office:
    environment:
      - MD2OFFICE_HOST=0.0.0.0
      - MD2OFFICE_PORT=8080
      - MD2OFFICE_LOG_LEVEL=info
      - MD2OFFICE_MAX_FILE_SIZE=52428800
```

**Docker Run:**

```bash
docker run -d \
  -e MD2OFFICE_HOST=0.0.0.0 \
  -e MD2OFFICE_PORT=8080 \
  -e MD2OFFICE_LOG_LEVEL=info \
  md2office:latest
```

**Environment File (.env):**

```bash
# Create .env file
cat > .env <<EOF
MD2OFFICE_HOST=0.0.0.0
MD2OFFICE_PORT=8080
MD2OFFICE_LOG_LEVEL=info
MD2OFFICE_MAX_FILE_SIZE=52428800
EOF

# Use with docker-compose
docker-compose --env-file .env up -d
```

## Volume Mounts

Volume mounts allow you to persist data and customize the application without rebuilding the Docker image.

### Overview

| Mount Point | Purpose | Mode | Required | Notes |
|-------------|---------|------|----------|-------|
| `/app/templates` | DOCX templates | `ro` (read-only) | Yes | Contains `.docx` template files |
| `/app/config` | Configuration files | `ro` (read-only) | Yes | `config.yaml`, `styles-mapping.yaml` |
| `/app/output` | Generated documents | `rw` (read-write) | Yes | API-generated DOCX files |
| `/app/src` | Source code | `ro` (read-only) | Dev only | Enables hot reload |
| `/app/temp` | Temporary files | `rw` (read-write) | No | Upload processing |

### Detailed Explanations

#### Templates Directory (`/app/templates`)

**Purpose:** Store DOCX template files used for document generation.

**Read-only:** Templates are only read by the application and should not be modified at runtime.

**Example Structure:**
```
templates/
├── default.docx
├── professional.docx
├── linagora.docx
└── custom/
    └── corporate.docx
```

**Docker Compose:**
```yaml
volumes:
  - ./templates:/app/templates:ro
```

**Docker Run:**
```bash
-v $(pwd)/templates:/app/templates:ro
```

#### Configuration Directory (`/app/config`)

**Purpose:** Configuration files for server settings and style mappings.

**Read-only:** Configuration is loaded at startup and should not change during runtime.

**Contents:**
- `config.yaml` - Server configuration
- `styles-mapping.yaml` - Default style mapping
- `styles-mapping-linagora.yaml` - LINAGORA-specific styles

**Docker Compose:**
```yaml
volumes:
  - ./config:/app/config:ro
```

#### Output Directory (`/app/output`)

**Purpose:** Store generated DOCX files from API conversions.

**Read-write:** Application writes converted documents here.

**Permissions:** The container runs as `appuser` (non-root), ensure the directory is writable:

```bash
# Create with correct permissions
mkdir -p output
chmod 755 output

# Or use Docker volume
docker volume create md2office-output
```

**Docker Compose:**
```yaml
volumes:
  - ./output:/app/output
  # OR use named volume
  - md2office-output:/app/output
```

#### Source Code Directory (`/app/src`) - Development Only

**Purpose:** Mount source code for hot reload during development.

**Read-only:** Source is read by the application.

**Docker Compose (dev profile):**
```yaml
volumes:
  - ./src:/app/src:ro
```

### Volume Best Practices

#### Production

```yaml
services:
  md2office:
    volumes:
      # Use read-only for config and templates
      - ./templates:/app/templates:ro
      - ./config:/app/config:ro
      # Use named volume for output (better for production)
      - md2office-output:/app/output

volumes:
  md2office-output:
    driver: local
```

#### Development

```yaml
services:
  md2office-dev:
    volumes:
      # Mount source for hot reload
      - ./src:/app/src:ro
      # Use local directories for easy access
      - ./templates:/app/templates:ro
      - ./config:/app/config:ro
      - ./output:/app/output
```

## Production vs Development

md2office includes separate Docker Compose services optimized for production and development.

### Comparison Table

| Feature | Production (`md2office`) | Development (`md2office-dev`) |
|---------|--------------------------|-------------------------------|
| **Auto-reload** | ❌ Disabled | ✅ Enabled (`--reload`) |
| **Log Level** | `info` | `debug` |
| **Source Mount** | ❌ Not mounted | ✅ Mounted (`./src:/app/src:ro`) |
| **Restart Policy** | `unless-stopped` | None (manual restart) |
| **Profile** | Default (always runs) | `dev` (must be specified) |
| **Workers** | 1 (configurable) | 1 (single worker for reload) |
| **Use Case** | Production deployment | Local development and testing |

### Production Service

**Optimized for:**
- Stability and reliability
- Automatic restart on failure
- Lower resource usage
- Production logging

**Configuration:**

```yaml
services:
  md2office:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - ./templates:/app/templates:ro
      - ./config:/app/config:ro
      - ./output:/app/output
    environment:
      - MD2OFFICE_HOST=0.0.0.0
      - MD2OFFICE_PORT=8080
      - MD2OFFICE_LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Start:**
```bash
docker-compose up -d
```

### Development Service

**Optimized for:**
- Rapid iteration with hot reload
- Verbose debugging output
- Easy troubleshooting
- Source code changes without rebuild

**Configuration:**

```yaml
services:
  md2office-dev:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - ./src:/app/src:ro      # Source code mount
      - ./templates:/app/templates:ro
      - ./config:/app/config:ro
      - ./output:/app/output
    environment:
      - MD2OFFICE_HOST=0.0.0.0
      - MD2OFFICE_PORT=8080
      - MD2OFFICE_LOG_LEVEL=debug
    command: ["uvicorn", "md2office.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
    profiles:
      - dev
```

**Start:**
```bash
docker-compose --profile dev up md2office-dev
```

### Switching Environments

```bash
# Stop production
docker-compose down

# Start development
docker-compose --profile dev up md2office-dev

# Stop development
docker-compose --profile dev down

# Restart production
docker-compose up -d
```

## Health Checks

Health checks monitor container health and enable automatic recovery.

### Docker Health Check

Defined in the Dockerfile and runs inside the container.

**Configuration:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()" || exit 1
```

**Parameters:**
- **interval:** `30s` - Check every 30 seconds
- **timeout:** `10s` - Fail if check takes longer than 10 seconds
- **start-period:** `5s` - Grace period before first check
- **retries:** `3` - Mark unhealthy after 3 consecutive failures

**Check Status:**
```bash
# View health status
docker inspect --format='{{.State.Health.Status}}' md2office

# View health check logs
docker inspect --format='{{json .State.Health}}' md2office | jq
```

### Docker Compose Health Check

Overrides or supplements the Dockerfile health check.

**Configuration:**

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**Custom Health Check:**

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 1m
  timeout: 5s
  retries: 3
  start_period: 30s
```

### Health Endpoint

The application exposes a health endpoint at `/health` and `/api/v1/health`.

**Test Manually:**

```bash
# Simple check
curl http://localhost:8080/health

# With status code
curl -i http://localhost:8080/health

# JSON response
curl -s http://localhost:8080/api/v1/health | jq
```

**Expected Response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-01-24T10:30:00Z"
}
```

### Integration with Orchestrators

#### Docker Swarm

```yaml
services:
  md2office:
    # ... other config
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Kubernetes

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: md2office
    image: md2office:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 30
      timeoutSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
```

## Resource Limits

Configure resource constraints to prevent excessive CPU or memory usage.

### Docker Compose Resource Limits

**Basic Limits:**

```yaml
services:
  md2office:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

**Recommended Production Limits:**

```yaml
services:
  md2office:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '2.0'        # Maximum 2 CPU cores
          memory: 1G         # Maximum 1GB RAM
        reservations:
          cpus: '1.0'        # Reserve 1 CPU core
          memory: 512M       # Reserve 512MB RAM
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

**High-Load Configuration:**

```yaml
services:
  md2office:
    # ... other config
    environment:
      - MD2OFFICE_WORKERS=4  # Multiple workers
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 2G
        reservations:
          cpus: '2.0'
          memory: 1G
```

### Docker Run Resource Limits

```bash
docker run -d \
  --name md2office \
  --cpus="2.0" \
  --memory="1g" \
  --memory-reservation="512m" \
  --restart=unless-stopped \
  -p 8080:8080 \
  md2office:latest
```

### Resource Limit Parameters

| Parameter | Description | Example | Notes |
|-----------|-------------|---------|-------|
| `--cpus` | Maximum CPU cores | `2.0` | Fractional values allowed (e.g., `0.5`) |
| `--memory` | Maximum memory | `1g`, `512m` | Hard limit, container killed if exceeded |
| `--memory-reservation` | Memory reservation | `512m` | Soft limit, best-effort reservation |
| `--memory-swap` | Total memory + swap | `2g` | Set to same as `--memory` to disable swap |
| `--pids-limit` | Max processes/threads | `100` | Prevent fork bombs |

### Monitoring Resource Usage

**Real-time Stats:**

```bash
# Single container
docker stats md2office

# All containers
docker stats

# JSON format
docker stats --no-stream --format "{{json .}}" md2office | jq
```

**Resource Usage Logs:**

```bash
# CPU and memory usage
docker exec md2office ps aux

# Detailed container inspect
docker inspect md2office | jq '.[0].HostConfig.Memory'
```

### Recommended Configurations

#### Small Deployment (1-10 users)

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
    reservations:
      cpus: '0.25'
      memory: 128M
```

#### Medium Deployment (10-100 users)

```yaml
environment:
  - MD2OFFICE_WORKERS=2
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
    reservations:
      cpus: '1.0'
      memory: 512M
```

#### Large Deployment (100+ users)

```yaml
environment:
  - MD2OFFICE_WORKERS=4
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 2G
    reservations:
      cpus: '2.0'
      memory: 1G
```

## Advanced Configuration

### Multi-Container Setup

**With Nginx Reverse Proxy:**

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - md2office
    restart: unless-stopped

  md2office:
    build: .
    expose:
      - "8080"
    environment:
      - MD2OFFICE_LOG_LEVEL=info
    restart: unless-stopped
```

**Nginx Configuration:**

```nginx
upstream md2office {
    server md2office:8080;
}

server {
    listen 80;
    server_name md2office.example.com;

    location / {
        proxy_pass http://md2office;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Increase upload size for large documents
        client_max_body_size 50M;
    }
}
```

### Persistent Storage

**Named Volumes:**

```yaml
services:
  md2office:
    # ... other config
    volumes:
      - templates:/app/templates:ro
      - config:/app/config:ro
      - output:/app/output

volumes:
  templates:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/md2office/templates
  config:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/md2office/config
  output:
    driver: local
```

### Environment-Specific Overrides

**Production (`docker-compose.prod.yml`):**

```yaml
services:
  md2office:
    environment:
      - MD2OFFICE_LOG_LEVEL=warning
      - MD2OFFICE_WORKERS=4
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
```

**Usage:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Logging Configuration

**JSON Logging:**

```yaml
services:
  md2office:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Syslog:**

```yaml
services:
  md2office:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://192.168.0.42:514"
        tag: "md2office"
```

## Troubleshooting

### Container Won't Start

**Problem:** Container exits immediately after starting.

**Diagnosis:**
```bash
# Check container logs
docker logs md2office

# Check last 50 lines
docker logs --tail 50 md2office

# Follow logs in real-time
docker logs -f md2office
```

**Common Causes:**

1. **Port already in use:**
   ```bash
   # Check what's using port 8080
   lsof -i :8080

   # Use different port
   docker run -p 9000:8080 md2office:latest
   ```

2. **Missing volumes:**
   ```bash
   # Verify directories exist
   ls -la templates config output

   # Create missing directories
   mkdir -p templates config output
   ```

3. **Permission issues:**
   ```bash
   # Container runs as appuser, fix permissions
   chmod 755 templates config output
   ```

### Health Check Failing

**Problem:** Container marked as unhealthy.

**Diagnosis:**
```bash
# Check health status
docker inspect --format='{{json .State.Health}}' md2office | jq

# Test health endpoint manually
docker exec md2office curl -f http://localhost:8080/health

# Check application logs
docker logs md2office | grep -i error
```

**Solutions:**

1. **Increase start period:**
   ```yaml
   healthcheck:
     start_period: 30s  # Give more time to start
   ```

2. **Check dependencies:**
   ```bash
   # Verify httpx is installed
   docker exec md2office python -c "import httpx; print(httpx.__version__)"
   ```

### High Memory Usage

**Problem:** Container consumes excessive memory.

**Diagnosis:**
```bash
# Monitor memory usage
docker stats md2office

# Check application memory
docker exec md2office ps aux
```

**Solutions:**

1. **Set memory limits:**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
   ```

2. **Reduce workers:**
   ```yaml
   environment:
     - MD2OFFICE_WORKERS=1
   ```

3. **Limit upload size:**
   ```yaml
   environment:
     - MD2OFFICE_MAX_FILE_SIZE=10485760  # 10MB
   ```

### Slow Performance

**Problem:** Conversions are taking too long.

**Solutions:**

1. **Increase CPU allocation:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
   ```

2. **Add more workers:**
   ```yaml
   environment:
     - MD2OFFICE_WORKERS=4
   ```

3. **Use SSD storage:**
   ```bash
   # Mount output to faster storage
   docker run -v /ssd/output:/app/output md2office:latest
   ```

### Volume Mount Issues

**Problem:** Templates or config not loading.

**Diagnosis:**
```bash
# Check mounted paths
docker exec md2office ls -la /app/templates
docker exec md2office ls -la /app/config

# Verify volume mounts
docker inspect md2office | jq '.[0].Mounts'
```

**Solutions:**

1. **Use absolute paths:**
   ```bash
   docker run -v /absolute/path/to/templates:/app/templates:ro md2office:latest
   ```

2. **Check SELinux (RHEL/CentOS):**
   ```bash
   # Add :z flag for SELinux
   docker run -v ./templates:/app/templates:ro,z md2office:latest
   ```

### Connection Refused

**Problem:** Cannot connect to API on port 8080.

**Diagnosis:**
```bash
# Check if port is exposed
docker ps | grep md2office

# Test from inside container
docker exec md2office curl http://localhost:8080/health

# Check firewall
sudo iptables -L -n | grep 8080
```

**Solutions:**

1. **Verify port mapping:**
   ```bash
   docker run -p 8080:8080 md2office:latest
   ```

2. **Check host binding:**
   ```yaml
   environment:
     - MD2OFFICE_HOST=0.0.0.0  # Not 127.0.0.1
   ```

### Logs Not Appearing

**Problem:** No logs visible with `docker logs`.

**Solutions:**

1. **Set log level:**
   ```yaml
   environment:
     - MD2OFFICE_LOG_LEVEL=debug
   ```

2. **Configure logging driver:**
   ```yaml
   logging:
     driver: "json-file"
   ```

### Build Failures

**Problem:** Docker build fails.

**Common Causes:**

1. **Network issues during dependency install:**
   ```bash
   # Build with no cache
   docker build --no-cache -t md2office:latest .
   ```

2. **Missing files:**
   ```bash
   # Verify required files exist
   ls -la pyproject.toml src/
   ```

## Support

| Resource | Link |
|----------|------|
| GitHub Issues | [github.com/mmaudet/md2office/issues](https://github.com/mmaudet/md2office/issues) |
| Documentation | [github.com/mmaudet/md2office](https://github.com/mmaudet/md2office) |
| User Guide | [README.md](README.md) |

## License

md2office is distributed under the Apache 2.0 license. See the [LICENSE](../LICENSE) file for details.

# Redis Connection Issues - Resolution

## Problem
The application was experiencing Redis connection errors with Upstash Redis, specifically:
- `ConnectionError: Connection closed by server`
- Celery tasks failing when trying to acquire Redis locks
- No connection pooling or retry logic
- Docker Compose configuration conflicts between local and remote Redis

## Root Causes
1. **New connections per operation**: Each Redis operation created a fresh connection
2. **No SSL configuration**: Upstash requires SSL but connections weren't properly configured
3. **No retry logic**: Connection drops weren't handled gracefully
4. **No connection pooling**: Inefficient connection management
5. **Docker Compose conflicts**: Local Redis service conflicting with Upstash configuration
6. **Socket keepalive configuration**: Invalid socket options causing Celery worker crashes

## Solutions Implemented

### 1. Shared Redis Utility (`app/core/redis.py`)
- Created centralized Redis connection management
- Implemented connection pooling with proper SSL configuration
- Added automatic SSL detection for Upstash URLs
- Configured connection timeouts and retry settings

### 2. Enhanced Lock Service (`app/services/lock_service.py`)
- Added retry logic with exponential backoff
- Improved error handling for connection drops
- Uses shared Redis connection pool
- Graceful lock release even on connection errors

### 3. Updated Health Endpoint (`app/api/routes/health.py`)
- Uses shared Redis utility for consistency
- Better error handling for Redis connectivity checks

### 4. Enhanced Celery Configuration (`app/core/celery_app.py`)
- Added connection retry settings
- Removed problematic socket keepalive options that caused worker crashes
- Enhanced broker transport options for reliability
- Proper SSL configuration for Upstash

### 5. Content Pipeline Resilience (`app/services/content_pipeline_service.py`)
- Added retry logic around Redis lock acquisition
- Better error logging and handling
- Exponential backoff for failed attempts

### 6. Docker Compose Updates
- **`docker-compose.yml`**: Updated to use Upstash Redis (no local Redis service)
- **`docker-compose.local.yml`**: Alternative for local development with local Redis
- Removed dependency conflicts between services

## Key Configuration Changes

### Redis Connection Pool Settings
- **Max connections**: 20
- **Socket timeout**: 10 seconds
- **Connection timeout**: 10 seconds
- **Health check interval**: 30 seconds
- **Retry on timeout**: Enabled

### Celery Broker Settings
- **Connection retry**: Enabled
- **Max retries**: 10
- **Heartbeat**: 30 seconds
- **Removed problematic socket keepalive options**

### Docker Configuration
- **Production**: Uses Upstash Redis via `docker-compose.yml`
- **Local Development**: Optional local Redis via `docker-compose.local.yml`

## Testing
Run the test scripts to verify connectivity:
```bash
cd wng-backend

# Test Redis connectivity
python test_redis_connection.py

# Test Celery connectivity
python test_celery_connection.py
```

## Usage

### With Upstash Redis (Production/Default)
```bash
docker-compose up
```

### With Local Redis (Development)
```bash
docker-compose -f docker-compose.local.yml up
```

## Benefits
1. **Reliability**: Connection drops are handled gracefully with retries
2. **Performance**: Connection pooling reduces overhead
3. **Monitoring**: Better error logging and health checks
4. **Scalability**: Proper connection management supports higher loads
5. **Flexibility**: Support for both local and remote Redis configurations

## Future Considerations
- Monitor Redis connection metrics in production
- Consider implementing circuit breaker pattern for extreme failure scenarios
- Add Redis connection monitoring to application metrics
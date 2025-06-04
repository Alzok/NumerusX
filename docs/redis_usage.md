# Redis Usage in NumerusX

## Overview

Redis is used as a caching and session store in NumerusX for improved performance and data management. This document outlines how Redis is configured and used throughout the application.

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password_here

# Connection pool settings
REDIS_MAX_CONNECTIONS=20
REDIS_RETRY_ON_TIMEOUT=true
REDIS_SOCKET_KEEPALIVE=true
```

### Application Configuration

Redis is configured in `app/config.py`:

```python
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
```

## Use Cases

### 1. MarketDataProvider Cache

**Purpose**: Cache market data to reduce API calls to external services
**TTL**: 30 seconds for price data, 5 minutes for historical data

```python
# Cache key pattern: market:{token_pair}:{data_type}
# Examples:
# market:SOL/USDC:price
# market:SOL/USDC:ohlcv_1h
# market:SOL/USDC:volume_24h
```

**Implementation**:
```python
import redis
from app.config import Config

redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)

# Store market data
redis_client.setex("market:SOL/USDC:price", 30, json.dumps(price_data))

# Retrieve market data
cached_data = redis_client.get("market:SOL/USDC:price")
if cached_data:
    price_data = json.loads(cached_data)
```

### 2. JupiterApiClient Cache

**Purpose**: Cache Jupiter API responses to respect rate limits
**TTL**: 10 seconds for quotes, 60 seconds for token info

```python
# Cache key pattern: jupiter:{endpoint}:{params_hash}
# Examples:
# jupiter:quote:a1b2c3d4e5f6...
# jupiter:swap:f6e5d4c3b2a1...
```

**Benefits**:
- Reduces API calls to Jupiter
- Improves response times
- Prevents rate limiting issues

### 3. User Sessions

**Purpose**: Store user authentication sessions and preferences
**TTL**: 24 hours for JWT sessions

```python
# Cache key pattern: session:{user_id}:{session_id}
# Examples:
# session:admin:sess_abc123
# session:admin:preferences
```

**Stored Data**:
- JWT token validation cache
- User preferences (theme, language, etc.)
- Trading settings per user

### 4. Rate Limiting

**Purpose**: Implement API rate limiting using FastAPI-Limiter
**Configuration**: Uses Redis as the backend store

```python
# Rate limiting patterns:
# rate_limit:{endpoint}:{user_id}:{time_window}
# Examples:
# rate_limit:/api/v1/trades:admin:60s
# rate_limit:/api/v1/bot/control:admin:60s
```

**Implementation**:
```python
from fastapi_limiter.depends import RateLimiter

@router.post("/trades", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_trade():
    # Limited to 10 requests per minute
    pass
```

### 5. Log Buffer

**Purpose**: Buffer logs before writing to persistent storage
**TTL**: 1 hour

```python
# Cache key pattern: logs:{module}:{level}:{timestamp}
# Examples:
# logs:trading_engine:ERROR:2024-01-15T10:30:00
# logs:ai_agent:INFO:2024-01-15T10:30:00
```

**Benefits**:
- Reduces disk I/O
- Enables real-time log streaming
- Provides log aggregation capabilities

### 6. AI Decision Cache

**Purpose**: Cache AI decision computation results
**TTL**: 5 minutes

```python
# Cache key pattern: ai_decision:{input_hash}
# Examples:
# ai_decision:market_state_abc123
```

**Use Case**: When similar market conditions occur, reuse previous AI analysis to speed up decision making.

## Connection Management

### Redis Client Initialization

```python
import redis.asyncio as redis
from app.config import Config

async def get_redis_client():
    """Get async Redis client with connection pooling."""
    return redis.from_url(
        Config.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
        retry_on_timeout=True,
        socket_keepalive=True
    )
```

### Connection Pool

Redis uses connection pooling to efficiently manage connections:

- **Max Connections**: 20 (configurable)
- **Connection Timeout**: 5 seconds
- **Socket Keepalive**: Enabled
- **Retry on Timeout**: Enabled

## Data Structures Used

### 1. Strings (most common)
- Simple key-value caching
- JSON serialized objects
- Session tokens

### 2. Hash Maps
- User preferences
- Configuration settings
- Structured data storage

### 3. Lists
- Log buffers
- Event queues
- Recent data history

### 4. Sets
- Active user sessions
- Feature flags
- Unique counters

### 5. Sorted Sets
- Rate limiting counters
- Time-based rankings
- Leaderboards

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Memory Usage**: Monitor Redis memory consumption
2. **Connection Count**: Track active connections
3. **Hit Rate**: Cache hit/miss ratio
4. **Response Time**: Redis operation latency

### Redis CLI Commands for Monitoring

```bash
# Check memory usage
redis-cli INFO memory

# Check connected clients
redis-cli INFO clients

# Monitor commands in real-time
redis-cli MONITOR

# Check keyspace
redis-cli INFO keyspace

# Get cache statistics
redis-cli INFO stats
```

### Maintenance Tasks

1. **Key Expiration**: Ensure TTL is set appropriately
2. **Memory Management**: Monitor and clear unused keys
3. **Connection Cleanup**: Monitor connection pool health
4. **Backup**: Regular Redis data backup (if needed)

## Best Practices

### 1. Key Naming Convention
- Use descriptive prefixes: `market:`, `session:`, `logs:`
- Include relevant identifiers: user_id, token_pair, timestamp
- Keep keys readable and consistent

### 2. TTL Management
- Always set appropriate TTL for cached data
- Use shorter TTL for frequently changing data
- Longer TTL for relatively stable data

### 3. Error Handling
```python
try:
    data = await redis_client.get(key)
except redis.ConnectionError:
    # Fallback to database or API
    logger.warning("Redis unavailable, using fallback")
    data = await get_from_database(key)
```

### 4. Data Serialization
- Use JSON for complex objects
- Store strings directly for simple values
- Consider compression for large data

### 5. Performance
- Use pipelining for bulk operations
- Prefer hash maps for related data
- Monitor key space and cleanup regularly

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check Redis server status
   - Verify network connectivity
   - Check connection pool settings

2. **Memory Issues**
   - Monitor Redis memory usage
   - Check for keys without TTL
   - Implement key eviction policies

3. **High Latency**
   - Check Redis server load
   - Monitor network latency
   - Optimize key access patterns

### Debug Commands

```bash
# Check if Redis is running
redis-cli ping

# List all keys (be careful in production)
redis-cli KEYS "*"

# Check specific key TTL
redis-cli TTL "market:SOL/USDC:price"

# Get key information
redis-cli TYPE "session:admin:sess_abc123"
redis-cli OBJECT ENCODING "market:SOL/USDC:price"
```

## Docker Configuration

In `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
```

## Security Considerations

1. **Authentication**: Use Redis AUTH when possible
2. **Network**: Bind Redis to specific interfaces only
3. **Encryption**: Use Redis TLS in production
4. **Firewall**: Restrict Redis port access
5. **Data Sensitivity**: Don't store sensitive data in Redis without encryption

## Performance Tuning

### Redis Configuration

```conf
# /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
```

### Application Level

- Use connection pooling
- Implement circuit breakers
- Monitor cache hit rates
- Optimize key access patterns

This Redis setup provides a robust caching layer that significantly improves NumerusX performance while maintaining data consistency and reliability. 
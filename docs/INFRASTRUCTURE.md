# Infrastructure connections

Three separate services, each with a clear purpose:

| Store      | Module                         | Purpose |
|-----------|--------------------------------|---------|
| PostgreSQL | `app.infrastructure.postgres`  | Relational data, SQLAlchemy ORM, Alembic migrations |
| MongoDB    | `app.infrastructure.mongo`     | Documents, flexible payloads, analytics, logs |
| Redis      | `app.infrastructure.redis_service` | Cache, rate limits, pub/sub, queue/session helpers |

## Environment variables

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/supplier_saas
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=supplier_saas
REDIS_URL=redis://localhost:6379/0
```

Docker Compose sets these to the `db`, `mongo`, and `redis` services.

## Usage in FastAPI

```python
from app.infrastructure.deps import DbSession, MongoDatabase, RedisClient

@router.post("/event")
def log_event(db: DbSession, mongo: MongoDatabase, r: RedisClient):
    r.incr("events:count")
    mongo["app_events"].insert_one({"source": "api"})
    # ... use db for SQLAlchemy ...
```

Lower-level access:

```python
from app.infrastructure.postgres import get_postgres_service
from app.infrastructure.mongo import get_mongo_service
from app.infrastructure.redis_service import get_redis_service

pg = get_postgres_service()
mongo = get_mongo_service()
redis_svc = get_redis_service()

pg.health_check()
mongo.get_collection("my_collection").find_one({})
redis_svc.client.get("key")
```

## Named MongoDB collection dependency

```python
from fastapi import Depends
from app.infrastructure.mongo import get_mongo_collection

@router.get("/logs")
def logs(coll=Depends(get_mongo_collection("request_logs"))):
    return list(coll.find().limit(10))
```

## Lifecycle

`main.py` lifespan connects all three at startup and disconnects on shutdown. Readiness: `GET /health/ready` checks PostgreSQL, MongoDB, and Redis.

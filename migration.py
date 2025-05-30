import redis
import json
import os
from dotenv import load_dotenv
load_dotenv()
URL=os.getenv('UPSTASH_URL')
PASS=os.getenv('UPSTASH_PASS')
import redis
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to local Redis (Docker)
r_local = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Connect to Upstash Redis
r_upstash = redis.Redis(
    host=URL,  # e.g., 'your-db.upstash.io'
    port=6379,
    password=PASS,
    ssl=True,
    decode_responses=True
)

keys = r_local.keys("*")
print(f"Found {len(keys)} keys")

for key in keys:
    key_type = r_local.type(key)
    print(f"Migrating {key} ({key_type})...")

    try:
        if key_type == 'string':
            value = r_local.get(key)
            r_upstash.set(key, value)

        elif key_type == 'hash':
            value = r_local.hgetall(key)
            if value:
                r_upstash.hset(key, mapping=value)

        elif key_type == 'list':
            values = r_local.lrange(key, 0, -1)
            if values:
                r_upstash.rpush(key, *values)

        elif key_type == 'set':
            members = r_local.smembers(key)
            if members:
                r_upstash.sadd(key, *members)

        elif key_type == 'zset':
            members = r_local.zrange(key, 0, -1, withscores=True)
            if members:
                r_upstash.zadd(key, dict(members))

        else:
            print(f"Skipping unsupported type: {key_type}")
    except Exception as e:
        print(f"❌ Failed to migrate {key}: {e}")
    else:
        print(f"✅ Migrated {key}")
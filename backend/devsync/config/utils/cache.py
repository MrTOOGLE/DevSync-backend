from django_redis import get_redis_connection

def delete_pattern(pattern):
    conn = get_redis_connection("default")
    keys = conn.keys(f":1:{pattern}")
    if keys:
        conn.delete(*keys)

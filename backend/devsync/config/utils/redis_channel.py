from channels_redis.core import RedisChannelLayer
from django.utils import timezone


class ExtendedRedisChannelLayer(RedisChannelLayer):

    async def get_group_channels(self, group):
        key = self._group_key(group)
        connection = self.connection(self.consistent_hash(group))
        await connection.zremrangebyscore(
            key, min=0, max=int(timezone.now().timestamp()) - self.group_expiry
        )

        return [x.decode("utf8") for x in await connection.zrange(key, 0, -1)]

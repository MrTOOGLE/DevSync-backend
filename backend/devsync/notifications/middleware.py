from channels.db import database_sync_to_async


class TokenBasedAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_params = dict(
            param.split("=")
            for param in scope.get("query_string", b"").decode().split("&")
            if "=" in param
        )
        token_key = query_params.get("token", None)

        if token_key is None:
            scope["user"] = None
        else:
            scope["user"] = await self.get_user_from_token(token_key)

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        from rest_framework.authtoken.models import Token

        try:
            token = Token.objects.select_related("user").get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

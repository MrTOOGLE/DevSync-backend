from rest_framework.exceptions import ParseError


class LazyContentType:
    def __init__(self, app_label: str, model: str):
        self._app_label = app_label
        self._model = model
        self._content_type = None

    def __call__(self):
        if self._content_type is None:
            self._content_type = self._load_content_type()
        return self._content_type

    def _load_content_type(self):
        from django.contrib.contenttypes.models import ContentType
        try:
            return ContentType.objects.get(app_label=self._app_label, model=self._model)
        except (ValueError, ContentType.DoesNotExist) as e:
            raise ParseError(f"Invalid content type: {str(e)}")

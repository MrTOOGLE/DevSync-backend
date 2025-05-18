from rest_framework import renderers, status


class ListRenderer(renderers.JSONRenderer):
    wrapper_key = 'items'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        view = renderer_context.get('view') if renderer_context else None
        if renderer_context:
            response = renderer_context.get('response')
            if response and not status.is_success(response.status_code):
                return super().render(data, accepted_media_type, renderer_context)
        action = getattr(view, 'action', None)

        if action == 'list':
            data = {self.wrapper_key: data}

        return super().render(data, accepted_media_type, renderer_context)

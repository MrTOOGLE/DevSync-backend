from rest_framework import renderers


class ListRenderer(renderers.JSONRenderer):
    wrapper_key = 'items'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        view = renderer_context.get('view') if renderer_context else None
        action = getattr(view, 'action', None)

        if action == 'list':
            data = {self.wrapper_key: data}

        return super().render(data, accepted_media_type, renderer_context)


class VotingListRenderer(ListRenderer):
    wrapper_key = 'votings'


class VotingOptionListRenderer(ListRenderer):
     wrapper_key = 'options'


class VotingOptionChoiceListRenderer(ListRenderer):
    wrapper_key = 'choices'


class VotingCommentListRenderer(ListRenderer):
    wrapper_key = 'comments'
    
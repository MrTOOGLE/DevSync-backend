from rest_framework import renderers


class ListRenderer(renderers.JSONRenderer):
    wrapper_key = 'items'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        view = renderer_context.get('view') if renderer_context else None
        action = getattr(view, 'action', None)

        if action == 'list':
            data = {self.wrapper_key: data}

        return super().render(data, accepted_media_type, renderer_context)


class ProjectListRenderer(ListRenderer):
    wrapper_key = 'projects'


class ProjectMemberListRenderer(ListRenderer):
    wrapper_key = 'members'


class ProjectInvitationListRenderer(ListRenderer):
    wrapper_key = 'invitations'


class DepartmentListRenderer(ListRenderer):
    wrapper_key = 'departments'


class RoleListRenderer(ListRenderer):
    wrapper_key = 'roles'

from config.utils.renderers import ListRenderer


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

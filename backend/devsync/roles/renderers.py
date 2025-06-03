from config.utils.renderers import ListRenderer


class RoleListRenderer(ListRenderer):
    wrapper_key = 'roles'


class RolePermissionsRenderer(ListRenderer):
    wrapper_key = 'permissions'

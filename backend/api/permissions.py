"""项目自定义角色权限类。"""

from rest_framework import permissions


class IsSystemAdmin(permissions.BasePermission):
    """仅允许系统管理员访问。"""

    def has_permission(self, request, view):
        # 统一要求先登录，再校验角色。
        return request.user.is_authenticated and request.user.role == "system_admin"


class IsCommunityAdmin(permissions.BasePermission):
    """仅允许社区管理员访问。"""

    def has_permission(self, request, view):
        # 社区管理员接口最小权限边界。
        return request.user.is_authenticated and request.user.role == "community_admin"


class IsVolunteer(permissions.BasePermission):
    """仅允许志愿者访问。"""

    def has_permission(self, request, view):
        # 志愿者端专用接口权限。
        return request.user.is_authenticated and request.user.role == "volunteer"


class IsSystemOrCommunityAdmin(permissions.BasePermission):
    """允许系统管理员或社区管理员访问。"""

    def has_permission(self, request, view):
        # 管理端公共接口使用该复合权限。
        return request.user.is_authenticated and request.user.role in ["system_admin", "community_admin"]

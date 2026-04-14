"""管理后台注册配置。

用于在管理后台中快速查看与维护核心业务数据。
"""

from django.contrib import admin

from .models import (
    User,
    Community,
    CommunityChangeRequest,
    ActivityType,
    Activity,
    Registration,
    Attendance,
    Notice,
    Evaluation,
    ActivityComment,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """用户管理后台展示配置。"""

    list_display = ("id", "username", "real_name", "role", "community", "phone", "is_active")
    list_filter = ("role", "community", "is_active")
    search_fields = ("username", "real_name", "phone")


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    """社区管理后台展示配置。"""

    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """活动管理后台展示配置。"""

    list_display = ("id", "title", "community", "activity_type", "review_status", "status", "start_time", "created_by")
    list_filter = ("review_status", "status", "community", "activity_type")
    search_fields = ("title", "location")


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    """活动类型后台展示配置。"""

    list_display = ("id", "name", "sort_order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(CommunityChangeRequest)
class CommunityChangeRequestAdmin(admin.ModelAdmin):
    """社区变更申请后台展示配置。"""

    list_display = ("id", "applicant", "from_community", "to_community", "status", "applied_at", "reviewed_by")
    list_filter = ("status", "from_community", "to_community")
    search_fields = ("applicant__username", "applicant__real_name", "reason", "review_note")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """报名记录后台展示配置。"""

    list_display = ("id", "activity", "volunteer", "status", "apply_time", "reviewed_by")
    list_filter = ("status",)
    search_fields = ("activity__title", "volunteer__real_name")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """签到工时后台展示配置。"""

    list_display = ("id", "registration", "check_in_time", "check_out_time", "hours", "approved_hours", "status")
    list_filter = ("status",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    """公告后台展示配置。"""

    list_display = ("id", "title", "community", "created_by", "publish_time")
    search_fields = ("title", "content")


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """活动评价后台展示配置。"""

    list_display = ("id", "activity", "volunteer", "rating", "created_at")
    list_filter = ("rating",)


@admin.register(ActivityComment)
class ActivityCommentAdmin(admin.ModelAdmin):
    """活动评论后台展示配置。"""

    list_display = ("id", "activity", "author", "parent", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("content", "author__username", "author__real_name", "activity__title")


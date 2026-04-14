"""接口路由总入口。

- 使用默认路由器注册各业务资源。
- 额外挂载令牌刷新接口。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api import views

# 统一注册业务资源路由。
router = DefaultRouter()
# 用户管理、登录、个人资料等接口。
router.register(r"users", views.UserViewSet, basename="user")
# 社区主数据维护接口。
router.register(r"communities", views.CommunityViewSet, basename="community")
# 志愿者社区变更申请与审核接口。
router.register(r"community-change-requests", views.CommunityChangeRequestViewSet, basename="community-change-request")
# 活动类型字典维护接口。
router.register(r"activity-types", views.ActivityTypeViewSet, basename="activity-type")
# 活动发布、审核、生命周期流转接口。
router.register(r"activities", views.ActivityViewSet, basename="activity")
# 活动报名接口。
router.register(r"registrations", views.RegistrationViewSet, basename="registration")
# 签到签退与工时审核接口。
router.register(r"attendances", views.AttendanceViewSet, basename="attendance")
# 公告发布与查询接口。
router.register(r"notices", views.NoticeViewSet, basename="notice")
# 活动评价接口。
router.register(r"evaluations", views.EvaluationViewSet, basename="evaluation")
# 活动评论与回复接口。
router.register(r"activity-comments", views.ActivityCommentViewSet, basename="activity-comment")
# 管理员操作审计日志接口。
router.register(r"operation-logs", views.OperationLogViewSet, basename="operation-log")
# 统计看板接口（按角色返回不同口径）。
router.register(r"stats", views.StatisticsViewSet, basename="stats")

urlpatterns = [
    # 业务接口使用统一前缀。
    path("", include(router.urls)),
    # 刷新访问令牌接口
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]


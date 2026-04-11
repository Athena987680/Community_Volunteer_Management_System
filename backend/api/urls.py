from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"communities", views.CommunityViewSet, basename="community")
router.register(r"activity-types", views.ActivityTypeViewSet, basename="activity-type")
router.register(r"activities", views.ActivityViewSet, basename="activity")
router.register(r"registrations", views.RegistrationViewSet, basename="registration")
router.register(r"attendances", views.AttendanceViewSet, basename="attendance")
router.register(r"notices", views.NoticeViewSet, basename="notice")
router.register(r"evaluations", views.EvaluationViewSet, basename="evaluation")
router.register(r"activity-comments", views.ActivityCommentViewSet, basename="activity-comment")
router.register(r"stats", views.StatisticsViewSet, basename="stats")

urlpatterns = [
    path("", include(router.urls)),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

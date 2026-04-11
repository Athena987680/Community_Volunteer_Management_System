from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import authenticate
from django.db.models import Q, Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Community, ActivityType, Activity, Registration, Attendance, Notice, Evaluation, ActivityComment
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserManageSerializer,
    UserProfileSerializer,
    CommunitySerializer,
    ActivityTypeSerializer,
    ActivitySerializer,
    RegistrationSerializer,
    AttendanceSerializer,
    NoticeSerializer,
    EvaluationSerializer,
    ActivityCommentSerializer,
)

DECIMAL_ZERO = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))


def is_system_admin(user):
    return user.is_authenticated and user.role == "system_admin"


def is_community_admin(user):
    return user.is_authenticated and user.role == "community_admin"


def is_volunteer(user):
    return user.is_authenticated and user.role == "volunteer"


def is_manager(user):
    return is_system_admin(user) or is_community_admin(user)


def ensure_manager(user):
    if not is_manager(user):
        raise PermissionDenied("仅管理员可操作")


def ensure_system_admin(user):
    if not is_system_admin(user):
        raise PermissionDenied("仅系统管理员可操作")


def calc_profile_completed(user):
    base_completed = bool(
        user.real_name
        and user.gender
        and user.phone
        and user.age
    )
    if not base_completed:
        return False
    if user.role in ["volunteer", "community_admin"]:
        return bool(user.community_id)
    return True


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("community").all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == "register":
            return UserRegisterSerializer
        if self.action in ["create", "update", "partial_update"] and is_system_admin(self.request.user):
            return UserManageSerializer
        if self.action in ["me", "update_profile"]:
            return UserProfileSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["register", "login"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if is_system_admin(user):
            return User.objects.select_related("community").all()
        return User.objects.select_related("community").filter(id=user.id)

    def create(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if is_system_admin(request.user):
            return super().update(request, *args, **kwargs)
        instance = self.get_object()
        if instance.id != request.user.id:
            raise PermissionDenied("只能修改自己的资料")
        serializer = UserProfileSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        extra = {}
        if instance.role == "system_admin":
            extra["community"] = None
            extra["skills"] = None
        elif instance.role == "community_admin":
            extra["skills"] = None
        serializer.save(**extra)
        instance.profile_completed = calc_profile_completed(instance)
        instance.save(update_fields=["profile_completed"])
        return Response(UserSerializer(instance, context={"request": request}).data)

    def partial_update(self, request, *args, **kwargs):
        if is_system_admin(request.user):
            return super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        if instance.id != request.user.id:
            raise PermissionDenied("只能修改自己的资料")
        serializer = UserProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        extra = {}
        if instance.role == "system_admin":
            extra["community"] = None
            extra["skills"] = None
        elif instance.role == "community_admin":
            extra["skills"] = None
        serializer.save(**extra)
        instance.profile_completed = calc_profile_completed(instance)
        instance.save(update_fields=["profile_completed"])
        return Response(UserSerializer(instance, context={"request": request}).data)

    def destroy(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        message = "注册成功，请登录后完善资料"
        if user.role == "community_admin":
            message = "社区管理员注册申请已提交，等待系统管理员审核"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)
        if user.role == "community_admin" and user.approval_status != "approved":
            if user.approval_status == "pending":
                return Response({"error": "社区管理员账号待系统管理员审核"}, status=status.HTTP_403_FORBIDDEN)
            return Response({"error": "社区管理员账号审核未通过，请联系系统管理员"}, status=status.HTTP_403_FORBIDDEN)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data,
            }
        )

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], url_path="update-profile")
    def update_profile(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        extra = {}
        if request.user.role == "system_admin":
            extra["community"] = None
            extra["skills"] = None
        elif request.user.role == "community_admin":
            extra["skills"] = None
        serializer.save(**extra)
        request.user.profile_completed = calc_profile_completed(request.user)
        request.user.save(update_fields=["profile_completed"])
        return Response(UserSerializer(request.user, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        ensure_system_admin(request.user)
        target_user = self.get_object()
        if target_user.role != "community_admin":
            raise ValidationError("仅支持审核社区管理员账号")

        target_user.approval_status = "approved"
        target_user.approval_note = request.data.get("approval_note", "系统管理员审核通过")
        target_user.is_active = True
        target_user.save(update_fields=["approval_status", "approval_note", "is_active"])
        return Response({"message": "社区管理员审核通过"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        ensure_system_admin(request.user)
        target_user = self.get_object()
        if target_user.role != "community_admin":
            raise ValidationError("仅支持审核社区管理员账号")

        target_user.approval_status = "rejected"
        target_user.approval_note = request.data.get("approval_note", "系统管理员审核拒绝")
        target_user.is_active = False
        target_user.save(update_fields=["approval_status", "approval_note", "is_active"])
        return Response({"message": "社区管理员审核已拒绝"})


class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and is_community_admin(user):
            return Community.objects.filter(id=user.community_id)
        return Community.objects.all()

    def create(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().destroy(request, *args, **kwargs)


class ActivityTypeViewSet(viewsets.ModelViewSet):
    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ActivityType.objects.all().order_by("sort_order", "id")
        if is_system_admin(self.request.user):
            return qs
        return qs.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        ensure_system_admin(request.user)
        return super().destroy(request, *args, **kwargs)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related("community", "activity_type", "created_by", "reviewer").all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        base_qs = Activity.objects.select_related("community", "activity_type", "created_by", "reviewer").all()
        if is_system_admin(user):
            return base_qs
        if is_community_admin(user):
            return base_qs.filter(community=user.community)
        return base_qs.filter(
            Q(status__in=["approved", "ongoing", "finished"])
            & (Q(allow_external=True) | Q(community=user.community))
        )

    def _check_manage_permission(self, user, activity):
        if is_system_admin(user):
            return
        if is_community_admin(user) and activity.community_id == user.community_id:
            return
        raise PermissionDenied("无权限操作该活动")

    def perform_create(self, serializer):
        user = self.request.user
        ensure_manager(user)

        community = serializer.validated_data.get("community")
        if is_community_admin(user):
            serializer.save(created_by=user, community=user.community, status="pending")
            return

        if not community:
            raise ValidationError("系统管理员创建活动时必须指定社区")
        serializer.save(created_by=user, status="pending")

    def perform_update(self, serializer):
        user = self.request.user
        activity = self.get_object()
        self._check_manage_permission(user, activity)
        if is_community_admin(user):
            if "status" in serializer.validated_data:
                raise ValidationError("社区管理员不能直接修改活动审核状态")
            serializer.save(community=user.community)
            return
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        activity = self.get_object()
        self._check_manage_permission(request.user, activity)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        ensure_system_admin(request.user)
        activity = self.get_object()
        decision = request.data.get("decision")
        note = request.data.get("review_note", "")

        if decision not in ["approved", "rejected"]:
            raise ValidationError("decision 只能是 approved 或 rejected")

        activity.status = decision
        activity.review_note = note
        activity.reviewer = request.user
        activity.reviewed_at = timezone.now()
        activity.save()
        return Response({"message": "活动审核完成", "status": activity.status})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        activity = self.get_object()
        self._check_manage_permission(request.user, activity)

        if activity.status not in ["approved", "ongoing"]:
            raise ValidationError("仅已通过审核的活动可以开始")

        activity.status = "ongoing"
        activity.save(update_fields=["status", "updated_at"])
        return Response({"message": "活动已开始"})

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        activity = self.get_object()
        self._check_manage_permission(request.user, activity)

        if activity.status not in ["ongoing", "approved"]:
            raise ValidationError("当前状态不可结束活动")

        activity.status = "finished"
        activity.save(update_fields=["status", "updated_at"])
        return Response({"message": "活动已结束"})


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.select_related(
        "activity", "activity__community", "activity__created_by", "volunteer", "reviewed_by"
    ).all()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Registration.objects.select_related(
            "activity", "activity__community", "activity__created_by", "volunteer", "reviewed_by"
        ).all()
        if is_volunteer(user):
            qs = qs.filter(volunteer=user)
            activity_id = self.request.query_params.get("activity")
            if activity_id:
                qs = qs.filter(activity_id=activity_id)
            return qs
        if is_community_admin(user):
            return qs.filter(activity__community=user.community)
        return qs

    def _check_review_permission(self, user, registration):
        if is_system_admin(user):
            return
        if (
            is_community_admin(user)
            and registration.activity.community_id == user.community_id
            and registration.activity.created_by_id == user.id
        ):
            return
        raise PermissionDenied("仅活动发布负责人或系统管理员可审核报名")

    def perform_create(self, serializer):
        user = self.request.user
        if not is_volunteer(user):
            raise PermissionDenied("仅志愿者可报名")

        activity = serializer.validated_data.get("activity")
        now = timezone.now()

        if activity.status != "approved":
            raise ValidationError("活动未通过审核，暂不可报名")
        if now > activity.deadline:
            raise ValidationError("报名已截止")
        if not activity.allow_external and user.community_id != activity.community_id:
            raise ValidationError("该活动不允许非本社区志愿者报名")

        existed = Registration.objects.filter(activity=activity, volunteer=user).exists()
        if existed:
            raise ValidationError("你已报名该活动")

        joined_count = Registration.objects.filter(
            activity=activity,
            status__in=["pending", "approved"],
        ).count()
        if joined_count >= activity.max_volunteers:
            raise ValidationError("报名人数已满")

        serializer.save(volunteer=user, status="pending")

    def update(self, request, *args, **kwargs):
        raise PermissionDenied("请使用专用审核接口修改报名状态")

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied("请使用专用审核接口修改报名状态")

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("不支持删除报名记录")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        registration = self.get_object()
        self._check_review_permission(request.user, registration)
        if registration.status != "pending":
            raise ValidationError("仅待审核报名可通过")
        approved_count = Registration.objects.filter(
            activity=registration.activity,
            status="approved",
        ).count()
        if approved_count >= registration.activity.max_volunteers:
            raise ValidationError("活动名额已满，无法继续通过报名")

        registration.status = "approved"
        registration.review_note = request.data.get("review_note", "")
        registration.reviewed_by = request.user
        registration.reviewed_at = timezone.now()
        registration.save()
        Attendance.objects.get_or_create(registration=registration)
        return Response({"message": "报名审核通过"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        registration = self.get_object()
        self._check_review_permission(request.user, registration)
        if registration.status != "pending":
            raise ValidationError("仅待审核报名可拒绝")

        registration.status = "rejected"
        registration.review_note = request.data.get("review_note", "")
        registration.reviewed_by = request.user
        registration.reviewed_at = timezone.now()
        registration.save()
        return Response({"message": "报名已拒绝"})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        registration = self.get_object()
        if registration.volunteer_id != request.user.id:
            raise PermissionDenied("只能取消自己的报名")
        if registration.status != "pending":
            raise ValidationError("仅待审核报名可取消")

        registration.status = "canceled"
        registration.save(update_fields=["status"])
        return Response({"message": "报名已取消"})

    @action(detail=True, methods=["get"], url_path="volunteer-profile")
    def volunteer_profile(self, request, pk=None):
        registration = self.get_object()
        if not is_manager(request.user):
            raise PermissionDenied("仅管理员可查看志愿者资料")
        return Response(UserSerializer(registration.volunteer, context={"request": request}).data)


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attendance.objects.select_related(
        "registration",
        "registration__activity",
        "registration__activity__community",
        "registration__volunteer",
        "reviewed_by",
    ).all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Attendance.objects.select_related(
            "registration",
            "registration__activity",
            "registration__activity__community",
            "registration__volunteer",
            "reviewed_by",
        ).all()
        if is_system_admin(user):
            return qs
        if is_community_admin(user):
            return qs.filter(registration__activity__community=user.community)
        return qs.filter(registration__volunteer=user)

    def _check_review_scope(self, user, attendance):
        if is_system_admin(user):
            return
        if is_community_admin(user) and attendance.registration.activity.community_id == user.community_id:
            return
        raise PermissionDenied("无权限审核该工时")

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        attendance = self.get_object()
        registration = attendance.registration
        user = request.user

        if registration.volunteer_id != user.id:
            raise PermissionDenied("只能为自己签到")
        if registration.status != "approved":
            raise ValidationError("报名尚未通过，不能签到")

        activity = registration.activity
        now = timezone.now()
        earliest = activity.start_time - timedelta(minutes=30)
        if now < earliest:
            raise ValidationError("未到签到时间")
        if now > activity.end_time:
            raise ValidationError("活动已结束，不能签到")
        if attendance.check_in_time:
            raise ValidationError("已签到，无需重复操作")

        attendance.check_in_time = now
        attendance.save(update_fields=["check_in_time"])

        return Response({"message": "签到成功"})

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        attendance = self.get_object()
        registration = attendance.registration
        user = request.user

        if registration.volunteer_id != user.id:
            raise PermissionDenied("只能为自己签退")
        if not attendance.check_in_time:
            raise ValidationError("尚未签到，不能签退")
        if attendance.check_out_time:
            raise ValidationError("已签退，无需重复操作")

        activity = registration.activity
        now = timezone.now()
        if now < activity.end_time:
            raise ValidationError("活动未结束，暂不可签退")

        attendance.check_out_time = now
        hours = Decimal((now - attendance.check_in_time).total_seconds() / 3600).quantize(Decimal("0.01"))
        if hours < Decimal("0.00"):
            hours = Decimal("0.00")

        attendance.hours = hours
        attendance.approved_hours = None
        attendance.status = "pending"
        attendance.reviewed_by = None
        attendance.review_note = ""
        attendance.reviewed_at = None
        attendance.save()

        return Response({"message": "签退成功，等待工时审核", "hours": float(hours)})

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        attendance = self.get_object()
        self._check_review_scope(request.user, attendance)

        if not attendance.check_out_time:
            raise ValidationError("志愿者尚未签退，不能审核工时")

        decision = request.data.get("decision", "confirmed")
        note = request.data.get("review_note", "")

        if decision not in ["confirmed", "rejected"]:
            raise ValidationError("decision 只能是 confirmed 或 rejected")

        if decision == "confirmed":
            approved_hours = request.data.get("approved_hours")
            if approved_hours is None:
                approved_hours = attendance.hours
            attendance.approved_hours = approved_hours
            attendance.status = "confirmed"
        else:
            attendance.approved_hours = Decimal("0.00")
            attendance.status = "rejected"

        attendance.review_note = note
        attendance.reviewed_by = request.user
        attendance.reviewed_at = timezone.now()
        attendance.save()
        return Response({"message": "工时审核完成", "status": attendance.status})


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.select_related("community", "created_by").all()
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Notice.objects.select_related("community", "created_by").all()
        if is_system_admin(user):
            return qs
        if is_community_admin(user):
            if self.request.query_params.get("manage_scope") == "1":
                if not user.community_id:
                    return qs.none()
                return qs.filter(community_id=user.community_id)
            return qs.filter(Q(community=user.community) | Q(community__isnull=True))
        return qs.filter(Q(community=user.community) | Q(community__isnull=True))

    def _check_manage_notice(self, user, notice=None):
        ensure_manager(user)
        if notice is None:
            return
        if is_system_admin(user):
            return
        if not user.community_id:
            raise PermissionDenied("社区管理员未绑定社区，无法管理公告")
        if notice.community_id == user.community_id:
            return
        raise PermissionDenied("社区管理员只能管理本社区公告，不能管理全局公告或其他社区公告")

    def perform_create(self, serializer):
        user = self.request.user
        ensure_manager(user)

        if is_community_admin(user):
            if not user.community_id:
                raise PermissionDenied("社区管理员未绑定社区，无法创建公告")
            serializer.save(created_by=user, community=user.community)
            return

        serializer.save(created_by=user)

    def perform_update(self, serializer):
        notice = self.get_object()
        self._check_manage_notice(self.request.user, notice)

        if is_community_admin(self.request.user):
            serializer.save(community=self.request.user.community)
            return
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        notice = self.get_object()
        self._check_manage_notice(request.user, notice)
        return super().destroy(request, *args, **kwargs)


class EvaluationViewSet(viewsets.ModelViewSet):
    queryset = Evaluation.objects.select_related("activity", "volunteer").all()
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Evaluation.objects.select_related("activity", "volunteer").all()
        if is_system_admin(user):
            return qs
        if is_community_admin(user):
            return qs.filter(activity__community=user.community)
        return qs.filter(volunteer=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not is_volunteer(user):
            raise PermissionDenied("仅志愿者可评价活动")

        activity = serializer.validated_data["activity"]
        if activity.status != "finished":
            raise ValidationError("活动未结束，暂不可评价")

        has_confirmed_attendance = Attendance.objects.filter(
            registration__activity=activity,
            registration__volunteer=user,
            status="confirmed",
        ).exists()
        if not has_confirmed_attendance:
            raise ValidationError("仅已完成并通过工时审核的志愿者可评价")

        serializer.save(volunteer=user)


class ActivityCommentViewSet(viewsets.ModelViewSet):
    queryset = ActivityComment.objects.select_related("activity", "author", "parent", "parent__author").all()
    serializer_class = ActivityCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ActivityComment.objects.select_related("activity", "author", "parent", "parent__author").all()
        activity_id = self.request.query_params.get("activity")
        if activity_id:
            qs = qs.filter(activity_id=activity_id)

        if is_system_admin(user):
            return qs

        if is_community_admin(user):
            return qs.filter(activity__community=user.community)

        return qs.filter(
            Q(activity__status__in=["approved", "ongoing", "finished"])
            & (Q(activity__allow_external=True) | Q(activity__community=user.community))
        )

    def perform_create(self, serializer):
        activity = serializer.validated_data["activity"]
        user = self.request.user
        parent = serializer.validated_data.get("parent")

        if parent and parent.activity_id != activity.id:
            raise ValidationError("回复评论必须属于同一个活动")

        if is_system_admin(user):
            serializer.save(author=user)
            return

        if is_community_admin(user):
            if activity.community_id != user.community_id:
                raise PermissionDenied("只能评论本社区活动")
            serializer.save(author=user)
            return

        if activity.status not in ["approved", "ongoing", "finished"]:
            raise PermissionDenied("当前活动不可评论")
        if not activity.allow_external and activity.community_id != user.community_id:
            raise PermissionDenied("无权限评论该活动")
        serializer.save(author=user)

    def update(self, request, *args, **kwargs):
        raise PermissionDenied("不支持修改评论，请删除后重新发布")

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied("不支持修改评论，请删除后重新发布")

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if request.user.role != "system_admin" and comment.author_id != request.user.id:
            raise PermissionDenied("仅评论发布者或系统管理员可以删除评论")
        if comment.is_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        comment.content = ""
        comment.is_deleted = True
        comment.deleted_at = timezone.now()
        comment.save(update_fields=["content", "is_deleted", "deleted_at", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class StatisticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _attendance_scope(self, user):
        qs = Attendance.objects.select_related(
            "registration",
            "registration__volunteer",
            "registration__activity",
            "registration__activity__community",
        )
        if is_system_admin(user):
            return qs
        if is_community_admin(user):
            return qs.filter(registration__activity__community=user.community)
        return qs.filter(registration__volunteer=user)

    def _activity_scope(self, user):
        qs = Activity.objects.select_related("community")
        if is_system_admin(user):
            return qs
        if is_community_admin(user):
            return qs.filter(community=user.community)
        return qs.filter(Q(allow_external=True) | Q(community=user.community))

    @action(detail=False, methods=["get"])
    def overview(self, request):
        user = request.user
        attendance_qs = self._attendance_scope(user)

        if is_volunteer(user):
            total_hours = attendance_qs.filter(status="confirmed").aggregate(
                total=Coalesce(Sum("approved_hours"), DECIMAL_ZERO)
            )["total"]
            data = {
                "role": user.role,
                "approved_registrations": Registration.objects.filter(
                    volunteer=user,
                    status="approved",
                ).count(),
                "pending_registrations": Registration.objects.filter(
                    volunteer=user,
                    status="pending",
                ).count(),
                "confirmed_hours": float(total_hours),
                "attended_activities": attendance_qs.filter(status="confirmed").count(),
            }
            return Response(data)

        data = {
            "role": user.role,
            "total_users": User.objects.count() if is_system_admin(user) else User.objects.filter(community=user.community).count(),
            "total_activities": self._activity_scope(user).count(),
            "pending_activity_reviews": self._activity_scope(user).filter(status="pending").count(),
            "pending_registration_reviews": Registration.objects.filter(
                activity__in=self._activity_scope(user),
                status="pending",
            ).count(),
            "pending_attendance_reviews": attendance_qs.filter(
                check_out_time__isnull=False,
                status="pending",
            ).count(),
            "confirmed_hours": float(
                attendance_qs.filter(status="confirmed").aggregate(
                    total=Coalesce(Sum("approved_hours"), DECIMAL_ZERO)
                )["total"]
            ),
        }
        return Response(data)

    @action(detail=False, methods=["get"])
    def service_ranking(self, request):
        user = request.user
        if not is_manager(user):
            raise PermissionDenied("仅管理员可查看排行榜")

        attendance_qs = self._attendance_scope(user).filter(status="confirmed")
        ranking = (
            attendance_qs.values(
                "registration__volunteer",
                "registration__volunteer__real_name",
                "registration__volunteer__community__name",
            )
            .annotate(total_hours=Coalesce(Sum("approved_hours"), DECIMAL_ZERO), activity_count=Count("id"))
            .order_by("-total_hours", "-activity_count")[:20]
        )

        data = [
            {
                "volunteer_id": item["registration__volunteer"],
                "volunteer_name": item["registration__volunteer__real_name"],
                "community_name": item["registration__volunteer__community__name"],
                "total_hours": float(item["total_hours"]),
                "activity_count": item["activity_count"],
            }
            for item in ranking
        ]
        return Response(data)

    @action(detail=False, methods=["get"])
    def community_distribution(self, request):
        user = request.user
        if not is_system_admin(user):
            raise PermissionDenied("仅系统管理员可查看社区分布")

        data = (
            Attendance.objects.filter(status="confirmed")
            .values("registration__activity__community", "registration__activity__community__name")
            .annotate(
                total_hours=Coalesce(Sum("approved_hours"), DECIMAL_ZERO),
                participant_count=Count("registration__volunteer", distinct=True),
            )
            .order_by("-total_hours")
        )

        result = [
            {
                "community_id": item["registration__activity__community"],
                "community_name": item["registration__activity__community__name"],
                "total_hours": float(item["total_hours"]),
                "participant_count": item["participant_count"],
            }
            for item in data
        ]
        return Response(result)






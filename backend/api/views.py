"""视图层：封装认证、权限、审核流程与统计接口。"""

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json

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
    OperationLog,
)
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserManageSerializer,
    UserProfileSerializer,
    CommunitySerializer,
    CommunityChangeRequestSerializer,
    ActivityTypeSerializer,
    ActivitySerializer,
    RegistrationSerializer,
    AttendanceSerializer,
    NoticeSerializer,
    EvaluationSerializer,
    ActivityCommentSerializer,
    OperationLogSerializer,
)

DECIMAL_ZERO = Value(0, output_field=DecimalField(max_digits=12, decimal_places=1))
HOUR_QUANT = Decimal("0.1")


def is_system_admin(user):
    """判断当前用户是否为系统管理员。"""
    return user.is_authenticated and user.role == "system_admin"


def is_community_admin(user):
    """判断当前用户是否为社区管理员。"""
    return user.is_authenticated and user.role == "community_admin"


def is_volunteer(user):
    """判断当前用户是否为志愿者。"""
    return user.is_authenticated and user.role == "volunteer"


def is_manager(user):
    """判断用户是否属于管理端角色。"""
    return is_system_admin(user) or is_community_admin(user)


def ensure_manager(user):
    """强制要求管理端角色，否则抛出权限异常。"""
    if not is_manager(user):
        raise PermissionDenied("仅管理员可操作")


def ensure_system_admin(user):
    """强制要求系统管理员角色，否则抛出权限异常。"""
    if not is_system_admin(user):
        raise PermissionDenied("仅系统管理员可操作")


def calc_profile_completed(user):
    """根据角色与必填项计算资料是否完善。"""
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


def validate_self_community_update(user, validated_data):
    """校验“本人修改所属社区”是否符合业务规则。"""
    if "community" not in validated_data:
        return
    target = validated_data.get("community")
    target_id = getattr(target, "id", None)
    current_id = user.community_id
    if target_id == current_id:
        return
    if user.role == "volunteer":
        if current_id is None and target_id is not None:
            return
        raise ValidationError("志愿者不能直接修改所属社区，请提交社区变更申请")
    if user.role == "community_admin":
        raise ValidationError("社区管理员不能自行修改所属社区，请联系系统管理员")


def round_hours(value):
    """统一工时小数精度为 1 位。"""
    if value is None:
        return None
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return decimal_value.quantize(HOUR_QUANT, rounding=ROUND_HALF_UP)


def auto_checkout_one(attendance, end_time=None):
    """对单条签到记录执行自动签退并计算工时。"""
    if attendance.check_out_time:
        return attendance
    activity_end_time = end_time or attendance.registration.activity.end_time
    raw_hours = Decimal((activity_end_time - attendance.check_in_time).total_seconds() / 3600)
    if raw_hours < Decimal("0"):
        raw_hours = Decimal("0")
    attendance.check_out_time = activity_end_time
    attendance.hours = round_hours(raw_hours)
    attendance.approved_hours = None
    attendance.status = "pending"
    attendance.reviewed_by = None
    attendance.review_note = ""
    attendance.reviewed_at = None
    attendance.save(
        update_fields=[
            "check_out_time",
            "hours",
            "approved_hours",
            "status",
            "reviewed_by",
            "review_note",
            "reviewed_at",
        ]
    )
    return attendance


def auto_checkout_expired_attendances():
    """批量处理已结束活动但未签退的记录。"""
    now = timezone.now()
    expired = (
        Attendance.objects.select_related("registration", "registration__activity")
        .filter(
            check_in_time__isnull=False,
            check_out_time__isnull=True,
            registration__activity__end_time__lte=now,
        )
        .all()
    )
    for attendance in expired:
        auto_checkout_one(attendance, attendance.registration.activity.end_time)


def derive_activity_status(activity, now=None):
    """根据当前时间推导活动生命周期状态。"""
    current = now or timezone.now()
    if current >= activity.end_time:
        return "finished"
    if current >= activity.start_time:
        return "ongoing"
    if current > activity.deadline:
        return "upcoming"
    return "recruiting"


ACTIVITY_STATUS_RANK = {
    # 用于防止状态被“回滚”（例如 finished 被重新覆盖为 recruiting）。
    "unopened": 0,
    "recruiting": 1,
    "upcoming": 2,
    "ongoing": 3,
    "finished": 4,
}


def sync_activity_instance_status(activity, now=None):
    """同步单个活动状态，避免状态回退。"""
    target_status = "unopened"
    if activity.review_status == "approved":
        target_status = derive_activity_status(activity, now=now)
        current_rank = ACTIVITY_STATUS_RANK.get(activity.status, 0)
        target_rank = ACTIVITY_STATUS_RANK.get(target_status, 0)
        if target_rank < current_rank:
            return activity
    if activity.status != target_status:
        activity.status = target_status
        activity.save(update_fields=["status", "updated_at"])
    return activity


def sync_activity_statuses():
    """批量同步活动状态。"""
    now = timezone.now()
    approved = Activity.objects.filter(review_status="approved")
    # 已结束
    approved.filter(end_time__lte=now).exclude(status="finished").update(status="finished")
    # 进行中
    approved.filter(start_time__lte=now, end_time__gt=now, status__in=["recruiting", "upcoming"]).update(status="ongoing")
    # 截止后待开始
    approved.filter(deadline__lt=now, start_time__gt=now, status="recruiting").update(status="upcoming")
    # 报名中
    approved.filter(deadline__gte=now, start_time__gt=now, status="unopened").update(status="recruiting")
    # 未通过审核的活动强制保持未开放
    Activity.objects.exclude(review_status="approved").exclude(status="unopened").update(status="unopened")


class SystemAdminOperationLogMixin:
    """为系统管理员写操作自动记录审计日志。"""
    LOG_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    MODULE_LABELS = {
        "user": "用户管理",
        "community": "社区管理",
        "community-change-request": "社区变更审核",
        "activity-type": "活动类型管理",
        "activity": "活动管理",
        "registration": "报名审核",
        "attendance": "工时审核",
        "notice": "公告管理",
        "evaluation": "活动评价",
        "activity-comment": "活动评论",
        "stats": "统计分析",
        "operation-log": "操作日志",
    }
    ACTION_LABELS = {
        "create": "新增",
        "update": "更新",
        "partial_update": "更新",
        "destroy": "删除",
        "approve": "通过",
        "reject": "拒绝",
        "review": "审核",
        "start": "开始活动",
        "finish": "结束活动",
        "confirm": "确认工时",
        "cancel": "取消",
        "check_in": "签到",
        "check_out": "签退",
    }
    SENSITIVE_KEYS = {"password", "access", "refresh", "token"}

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        self._create_operation_log(request, response)
        return response

    def _create_operation_log(self, request, response):
        try:
            if request.method not in self.LOG_METHODS:
                return
            # 仅记录系统管理员的写操作，避免日志噪音。
            if not is_system_admin(getattr(request, "user", None)):
                return

            basename = getattr(self, "basename", "") or "unknown"
            if basename == "operation-log":
                return

            module = self.MODULE_LABELS.get(basename, basename)
            action_name = self._resolve_action_name(request)
            target_id, target_display = self._resolve_target_info(response)
            detail_text = self._build_detail_text(request, response)

            OperationLog.objects.create(
                operator=request.user,
                operator_display=request.user.real_name or request.user.username,
                module=module,
                action=action_name,
                method=request.method,
                path=request.get_full_path()[:300],
                target_type=basename,
                target_id=target_id,
                target_display=(target_display or "")[:200] or None,
                status="success" if 200 <= response.status_code < 400 else "failed",
                status_code=response.status_code,
                ip_address=self._get_client_ip(request),
                detail=detail_text,
            )
        except Exception:
            # 操作日志记录失败不能影响业务接口返回。
            return

    def _resolve_action_name(self, request):
        action = getattr(self, "action", None)
        if not action:
            method_map = {
                "POST": "create",
                "PUT": "update",
                "PATCH": "partial_update",
                "DELETE": "destroy",
            }
            action = method_map.get(request.method, request.method.lower())
        return self.ACTION_LABELS.get(action, action)

    def _resolve_target_info(self, response):
        raw_target_id = self.kwargs.get(getattr(self, "lookup_field", "pk"))
        target_display = ""
        data = getattr(response, "data", None)
        if isinstance(data, dict):
            if not raw_target_id and data.get("id") is not None:
                raw_target_id = data.get("id")
            target_display = (
                data.get("title")
                or data.get("name")
                or data.get("username")
                or data.get("real_name")
                or data.get("message")
                or ""
            )
        target_id = None
        if raw_target_id is not None and str(raw_target_id).isdigit():
            target_id = int(raw_target_id)
        if not target_display and target_id is not None:
            target_display = f"ID={target_id}"
        return target_id, target_display

    def _build_detail_text(self, request, response):
        # 将请求体与错误响应做脱敏后写入 detail 字段，方便排障。
        payload = {
            "request": self._sanitize_payload(getattr(request, "data", None)),
        }
        if response.status_code >= 400:
            payload["response"] = self._sanitize_payload(getattr(response, "data", None))
        text = json.dumps(payload, ensure_ascii=False, default=str)
        if len(text) > 2000:
            return f"{text[:2000]}..."
        return text

    def _sanitize_payload(self, data):
        if data is None:
            return None

        if hasattr(data, "lists"):
            items = {}
            for key, values in data.lists():
                items[key] = [self._sanitize_value(key, value) for value in values]
                if len(items[key]) == 1:
                    items[key] = items[key][0]
            return items

        if isinstance(data, dict):
            return {key: self._sanitize_value(key, value) for key, value in data.items()}

        return str(data)

    def _sanitize_value(self, key, value):
        lowered = str(key).lower()
        if lowered in self.SENSITIVE_KEYS or "password" in lowered:
            return "***"
        if hasattr(value, "name") and hasattr(value, "size"):
            return f"<file:{value.name}>"
        if isinstance(value, (list, tuple)):
            return [self._sanitize_value(key, item) for item in value]
        return value

    def _get_client_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class UserViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """用户相关接口：注册、登录、个人资料、管理员审核。"""
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
        # 系统管理员可见全部用户，其余角色仅能访问自己。
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
        validate_self_community_update(instance, serializer.validated_data)
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
        validate_self_community_update(instance, serializer.validated_data)
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
        # 社区管理员账号登录前必须通过系统管理员审核。
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
        validate_self_community_update(request.user, serializer.validated_data)
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


class CommunityViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """社区管理接口。"""
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


class ActivityTypeViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """活动类型管理接口。"""
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


class CommunityChangeRequestViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """志愿者社区变更申请与审核接口。"""
    queryset = CommunityChangeRequest.objects.select_related(
        "applicant",
        "from_community",
        "to_community",
        "reviewed_by",
    ).all()
    serializer_class = CommunityChangeRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = CommunityChangeRequest.objects.select_related(
            "applicant",
            "from_community",
            "to_community",
            "reviewed_by",
        ).all()
        if is_system_admin(user):
            return qs
        if is_volunteer(user):
            return qs.filter(applicant=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if not is_volunteer(user):
            raise PermissionDenied("仅志愿者可申请变更社区")
        if not user.community_id:
            raise ValidationError("当前未绑定所属社区，无法发起变更申请")

        # 业务限制：同一用户只能有一条待审核申请。
        pending_exists = CommunityChangeRequest.objects.filter(applicant=user, status="pending").exists()
        if pending_exists:
            raise ValidationError("你有待审核的社区变更申请，请等待处理")

        # 业务限制：30 天内最多通过一次社区变更。
        now = timezone.now()
        latest_approved = (
            CommunityChangeRequest.objects.filter(applicant=user, status="approved", reviewed_at__isnull=False)
            .order_by("-reviewed_at")
            .first()
        )
        if latest_approved and latest_approved.reviewed_at + timedelta(days=30) > now:
            next_date = (latest_approved.reviewed_at + timedelta(days=30)).date().isoformat()
            raise ValidationError(f"社区变更申请30天内仅允许一次，下次可申请日期：{next_date}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_community = serializer.validated_data["to_community"]
        if to_community.id == user.community_id:
            raise ValidationError("目标社区不能与当前所属社区相同")

        serializer.save(applicant=user, from_community=user.community, status="pending")
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        raise PermissionDenied("不支持直接修改申请记录")

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied("不支持直接修改申请记录")

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("不支持删除申请记录")

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        ensure_system_admin(request.user)
        record = self.get_object()
        if record.status != "pending":
            raise ValidationError("仅待审核申请可操作")

        decision = request.data.get("decision")
        note = request.data.get("review_note", "")
        if decision not in ["approved", "rejected"]:
            raise ValidationError("decision 只能是 approved 或 rejected")

        now = timezone.now()
        if decision == "approved":
            applicant = record.applicant
            if applicant.role != "volunteer":
                raise ValidationError("仅志愿者支持社区变更审核")
            applicant.community = record.to_community
            applicant.profile_completed = calc_profile_completed(applicant)
            applicant.save(update_fields=["community", "profile_completed"])
            record.status = "approved"
        else:
            record.status = "rejected"

        record.review_note = note
        record.reviewed_by = request.user
        record.reviewed_at = now
        record.save(update_fields=["status", "review_note", "reviewed_by", "reviewed_at"])
        return Response({"message": "社区变更审核完成", "status": record.status})


class ActivityViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """活动发布、审核与进度控制接口。"""
    queryset = Activity.objects.select_related("community", "activity_type", "created_by", "reviewer").all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        # 每次查询前先同步活动状态，保证列表与详情一致。
        sync_activity_statuses()
        user = self.request.user
        base_qs = Activity.objects.select_related("community", "activity_type", "created_by", "reviewer").all()
        if is_system_admin(user):
            return base_qs
        if is_community_admin(user):
            return base_qs.filter(community=user.community)
        # 志愿者仅可见“已审核通过 + 符合社区参与范围”的活动。
        return base_qs.filter(
            Q(review_status="approved")
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
            serializer.save(created_by=user, community=user.community, review_status="pending", status="unopened")
            return

        if not community:
            raise ValidationError("系统管理员创建活动时必须指定社区")
        serializer.save(created_by=user, review_status="pending", status="unopened")

    def perform_update(self, serializer):
        user = self.request.user
        activity = self.get_object()
        self._check_manage_permission(user, activity)
        if is_community_admin(user):
            if "status" in serializer.validated_data or "review_status" in serializer.validated_data:
                raise ValidationError("社区管理员不能直接修改活动状态")
            updated_activity = serializer.save(community=user.community)
            sync_activity_instance_status(updated_activity)
            return
        if "status" in serializer.validated_data or "review_status" in serializer.validated_data:
            raise ValidationError("请使用审核接口或活动进度接口变更状态")
        updated_activity = serializer.save()
        sync_activity_instance_status(updated_activity)

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

        activity.review_status = decision
        if decision == "approved":
            activity.status = derive_activity_status(activity)
        else:
            activity.status = "unopened"
        activity.review_note = note
        activity.reviewer = request.user
        activity.reviewed_at = timezone.now()
        activity.save(update_fields=["review_status", "status", "review_note", "reviewer", "reviewed_at", "updated_at"])
        return Response({"message": "活动审核完成", "review_status": activity.review_status, "status": activity.status})

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        activity = self.get_object()
        self._check_manage_permission(request.user, activity)

        if activity.review_status != "approved":
            raise ValidationError("活动未通过审核，不能开始")
        if activity.status == "finished":
            raise ValidationError("活动已结束，不能重新开始")

        activity.status = "ongoing"
        activity.save(update_fields=["status", "updated_at"])
        return Response({"message": "活动已开始"})

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        activity = self.get_object()
        self._check_manage_permission(request.user, activity)

        if activity.review_status != "approved":
            raise ValidationError("活动未通过审核，不能结束")
        if activity.status == "finished":
            raise ValidationError("活动已结束，无需重复操作")

        activity.status = "finished"
        activity.save(update_fields=["status", "updated_at"])
        return Response({"message": "活动已结束"})


class RegistrationViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """报名与报名审核接口。"""
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
        # 社区管理员只能审核“自己发布且属于本社区”的活动报名。
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
        # 报名前先同步活动状态，防止时间跨越造成状态陈旧。
        sync_activity_instance_status(activity, now=now)

        if activity.review_status != "approved":
            raise ValidationError("活动未通过审核，暂不可报名")
        if activity.status != "recruiting":
            raise ValidationError("当前活动不在报名中")
        if now > activity.deadline:
            raise ValidationError("报名已截止")
        if not activity.allow_external and user.community_id != activity.community_id:
            raise ValidationError("该活动不允许非本社区志愿者报名")

        existed = Registration.objects.filter(activity=activity, volunteer=user).exists()
        if existed:
            raise ValidationError("你已报名该活动")

        # 名额统计包含 pending + approved，防止超卖。
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


class AttendanceViewSet(SystemAdminOperationLogMixin, viewsets.ReadOnlyModelViewSet):
    """签到签退与工时审核接口。"""
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
        # 自动补齐已结束活动的签退时间，减少人工漏操作。
        auto_checkout_expired_attendances()
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

        auto_checkout_one(attendance, activity.end_time)
        return Response({"message": "活动已结束，系统已自动签退", "hours": float(attendance.hours or 0)})

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        attendance = self.get_object()
        auto_checkout_expired_attendances()
        attendance.refresh_from_db()
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
            try:
                approved_hours_value = round_hours(approved_hours or Decimal("0"))
            except (InvalidOperation, TypeError, ValueError):
                raise ValidationError("approved_hours 必须是合法数字")
            if approved_hours_value < Decimal("0"):
                raise ValidationError("approved_hours 不能小于 0")
            attendance.approved_hours = approved_hours_value
            attendance.status = "confirmed"
        else:
            attendance.approved_hours = Decimal("0.0")
            attendance.status = "rejected"

        attendance.review_note = note
        attendance.reviewed_by = request.user
        attendance.reviewed_at = timezone.now()
        attendance.save()
        return Response({"message": "工时审核完成", "status": attendance.status})


class NoticeViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """公告管理接口。"""
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
                # 管理态只看“本社区可管理公告”。
                if not user.community_id:
                    return qs.none()
                return qs.filter(community_id=user.community_id)
            # 查看态可读“本社区 + 全局公告”。
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


class EvaluationViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """活动评价接口。"""
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
        sync_activity_instance_status(activity)
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


class ActivityCommentViewSet(SystemAdminOperationLogMixin, viewsets.ModelViewSet):
    """活动评论接口。"""
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
            Q(activity__review_status="approved")
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

        sync_activity_instance_status(activity)
        if activity.review_status != "approved":
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


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """系统管理员操作日志查询接口。"""
    queryset = OperationLog.objects.select_related("operator").all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ensure_system_admin(self.request.user)
        qs = OperationLog.objects.select_related("operator").all()
        module = self.request.query_params.get("module")
        action_name = self.request.query_params.get("action")
        status_value = self.request.query_params.get("status")
        keyword = self.request.query_params.get("keyword")

        if module:
            qs = qs.filter(module=module)
        if action_name:
            qs = qs.filter(action=action_name)
        if status_value:
            qs = qs.filter(status=status_value)
        if keyword:
            qs = qs.filter(
                Q(operator_display__icontains=keyword)
                | Q(target_display__icontains=keyword)
                | Q(path__icontains=keyword)
                | Q(detail__icontains=keyword)
            )
        return qs


class StatisticsViewSet(viewsets.ViewSet):
    """统计分析接口：概览、排行榜、社区分布。"""
    permission_classes = [IsAuthenticated]

    def _attendance_scope(self, user):
        qs = Attendance.objects.select_related(
            "registration",
            "registration__volunteer",
            "registration__activity",
            "registration__activity__community",
        )
        # 三种角色各自的数据可见范围。
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

        # 志愿者视角：以“个人报名与工时”指标为主。
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
                "confirmed_hours": float(round_hours(total_hours)),
                "attended_activities": attendance_qs.filter(status="confirmed").count(),
            }
            return Response(data)

        # 管理视角：聚焦待审核数量与整体服务产出。
        data = {
            "role": user.role,
            "total_users": User.objects.count() if is_system_admin(user) else User.objects.filter(community=user.community).count(),
            "total_activities": self._activity_scope(user).count(),
            "pending_activity_reviews": self._activity_scope(user).filter(review_status="pending").count(),
            "pending_registration_reviews": Registration.objects.filter(
                activity__in=self._activity_scope(user),
                status="pending",
            ).count(),
            "pending_attendance_reviews": attendance_qs.filter(
                check_out_time__isnull=False,
                status="pending",
            ).count(),
            "confirmed_hours": float(
                round_hours(
                    attendance_qs.filter(status="confirmed").aggregate(
                        total=Coalesce(Sum("approved_hours"), DECIMAL_ZERO)
                    )["total"]
                )
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
                "total_hours": float(round_hours(item["total_hours"])),
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
                "total_hours": float(round_hours(item["total_hours"])),
                "participant_count": item["participant_count"],
            }
            for item in data
        ]
        return Response(result)








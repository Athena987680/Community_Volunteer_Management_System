"""序列化器定义与输入校验规则。"""

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import DisallowedHost
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers

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

DECIMAL_ZERO = Value(0, output_field=DecimalField(max_digits=12, decimal_places=1))
HOUR_QUANT = Decimal("0.1")


def format_hours(value):
    """统一将工时值格式化为 1 位小数浮点数。"""
    if value is None:
        return None
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return float(decimal_value.quantize(HOUR_QUANT, rounding=ROUND_HALF_UP))


class UserSerializer(serializers.ModelSerializer):
    """用户信息展示序列化器。"""
    community_name = serializers.CharField(source="community.name", read_only=True)
    total_service_hours = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "real_name",
            "gender",
            "phone",
            "age",
            "avatar",
            "role",
            "community",
            "community_name",
            "skills",
            "total_service_hours",
            "is_active",
            "approval_status",
            "approval_note",
            "profile_completed",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_total_service_hours(self, obj):
        # 仅志愿者展示累计服务工时；管理角色返回空值。
        if obj.role != "volunteer":
            return None
        agg = Attendance.objects.filter(
            registration__volunteer=obj,
            status="confirmed",
        ).aggregate(total=Coalesce(Sum("approved_hours"), DECIMAL_ZERO))
        return format_hours(agg["total"]) if agg["total"] is not None else 0

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get("request")
        url = obj.avatar.url
        if request:
            try:
                return request.build_absolute_uri(url)
            except DisallowedHost:
                return url
        return url

    def to_representation(self, instance):
        # 按角色裁剪不适用字段，避免前端误展示。
        data = super().to_representation(instance)
        if instance.role == "system_admin":
            data["community"] = None
            data["community_name"] = None
            data["skills"] = None
            data["total_service_hours"] = None
        elif instance.role == "community_admin":
            data["skills"] = None
            data["total_service_hours"] = None
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器。"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "role",
            "community",
        ]

    def create(self, validated_data):
        # 社区管理员注册后需系统管理员审核。
        role = validated_data.get("role", "volunteer")
        validated_data["approval_status"] = "pending" if role == "community_admin" else "approved"
        validated_data["profile_completed"] = False
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def validate(self, attrs):
        role = attrs.get("role")
        if role not in ["volunteer", "community_admin"]:
            raise serializers.ValidationError("注册仅允许选择志愿者或社区管理员角色")
        if not attrs.get("community"):
            raise serializers.ValidationError("注册必须选择所属社区")
        return attrs


class UserManageSerializer(serializers.ModelSerializer):
    """系统管理员使用的用户管理序列化器。"""
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "real_name",
            "gender",
            "phone",
            "age",
            "avatar",
            "role",
            "community",
            "skills",
            "is_active",
            "approval_status",
            "approval_note",
            "profile_completed",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def validate(self, attrs):
        # 管理端统一做角色-字段一致性约束。
        role = attrs.get("role", getattr(self.instance, "role", None))
        community = attrs.get("community", getattr(self.instance, "community", None))
        if role in ["volunteer", "community_admin"] and not community:
            raise serializers.ValidationError("志愿者和社区管理员必须绑定所属社区")
        if role == "system_admin":
            attrs["community"] = None
            attrs["skills"] = None
            attrs["approval_status"] = "approved"
        if role == "community_admin":
            attrs["skills"] = None
        return attrs

    def validate_phone(self, value):
        if value in ["", None]:
            return None
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """当前用户个人资料更新序列化器。"""
    class Meta:
        model = User
        fields = ["real_name", "gender", "phone", "age", "community", "skills", "avatar"]

    def validate_phone(self, value):
        if value in ["", None]:
            return None
        return value


class CommunitySerializer(serializers.ModelSerializer):
    """社区序列化器。"""
    class Meta:
        model = Community
        fields = "__all__"


class CommunityChangeRequestSerializer(serializers.ModelSerializer):
    """社区变更申请序列化器。"""
    applicant_name = serializers.CharField(source="applicant.real_name", read_only=True)
    applicant_username = serializers.CharField(source="applicant.username", read_only=True)
    from_community_name = serializers.CharField(source="from_community.name", read_only=True)
    to_community_name = serializers.CharField(source="to_community.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.real_name", read_only=True)

    class Meta:
        model = CommunityChangeRequest
        fields = "__all__"
        read_only_fields = [
            "applicant",
            "from_community",
            "status",
            "review_note",
            "reviewed_by",
            "applied_at",
            "reviewed_at",
        ]

    def validate_reason(self, value):
        # 统一去除首尾空白，空字符串转 None。
        if value is None:
            return None
        text = value.strip()
        return text or None


class ActivityTypeSerializer(serializers.ModelSerializer):
    """活动类型序列化器。"""
    class Meta:
        model = ActivityType
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class ActivitySerializer(serializers.ModelSerializer):
    """活动序列化器，包含活动业务校验。"""
    community_name = serializers.CharField(source="community.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.real_name", read_only=True)
    reviewer_name = serializers.CharField(source="reviewer.real_name", read_only=True)
    approved_count = serializers.SerializerMethodField()
    type = serializers.CharField(source="activity_type.name", read_only=True)
    activity_type_name = serializers.CharField(source="activity_type.name", read_only=True)
    type_display = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = "__all__"
        read_only_fields = ["status", "review_status", "created_by", "reviewer", "reviewed_at", "created_at", "updated_at"]

    def get_approved_count(self, obj):
        return obj.registrations.filter(status="approved").count()

    def get_type_display(self, obj):
        if obj.activity_type and obj.activity_type.name == "其他" and obj.other_type:
            return f"其他（{obj.other_type}）"
        if obj.activity_type:
            return obj.activity_type.name
        return None

    def validate(self, attrs):
        # 编辑场景下需兼容“部分字段更新”。
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        deadline = attrs.get("deadline", getattr(self.instance, "deadline", None))
        activity_type = attrs.get("activity_type", getattr(self.instance, "activity_type", None))
        other_type = attrs.get("other_type", getattr(self.instance, "other_type", None))

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("结束时间必须晚于开始时间")
        if deadline and start_time and deadline > start_time:
            raise serializers.ValidationError("报名截止时间不能晚于活动开始时间")

        if not activity_type:
            raise serializers.ValidationError("请选择活动类型")

        if activity_type.name == "其他":
            # “其他”类型必须填写补充说明。
            other_type_text = (other_type or "").strip()
            if not other_type_text:
                raise serializers.ValidationError("选择“其他”时必须填写类型补充")
            attrs["other_type"] = other_type_text
        else:
            # 非“其他”类型不保留 other_type，避免脏数据。
            unchanged_existing_type = bool(self.instance and activity_type.id == getattr(self.instance.activity_type, "id", None))
            if not activity_type.is_active and not unchanged_existing_type:
                raise serializers.ValidationError("活动类型必须从系统启用类型中选择")
            attrs["other_type"] = None
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    """报名记录序列化器。"""
    activity_title = serializers.CharField(source="activity.title", read_only=True)
    activity_status = serializers.CharField(source="activity.status", read_only=True)
    volunteer_name = serializers.CharField(source="volunteer.real_name", read_only=True)
    community_name = serializers.CharField(source="activity.community.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.real_name", read_only=True)
    attendance_status = serializers.CharField(source="attendance.status", read_only=True)

    class Meta:
        model = Registration
        fields = "__all__"
        read_only_fields = ["volunteer", "apply_time", "reviewed_by", "reviewed_at"]


class AttendanceSerializer(serializers.ModelSerializer):
    """签到工时序列化器。"""
    volunteer = serializers.IntegerField(source="registration.volunteer.id", read_only=True)
    volunteer_name = serializers.CharField(source="registration.volunteer.real_name", read_only=True)
    activity = serializers.IntegerField(source="registration.activity.id", read_only=True)
    activity_title = serializers.CharField(source="registration.activity.title", read_only=True)
    community = serializers.IntegerField(source="registration.activity.community.id", read_only=True)
    community_name = serializers.CharField(source="registration.activity.community.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.real_name", read_only=True)

    class Meta:
        model = Attendance
        fields = "__all__"
        read_only_fields = [
            "hours",
            "approved_hours",
            "reviewed_by",
            "reviewed_at",
        ]

    def to_representation(self, instance):
        # 前端统一使用格式化后的小时数字（1 位小数）。
        data = super().to_representation(instance)
        data["hours"] = format_hours(instance.hours)
        data["approved_hours"] = format_hours(instance.approved_hours)
        return data


class NoticeSerializer(serializers.ModelSerializer):
    """公告序列化器。"""
    community_name = serializers.CharField(source="community.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.real_name", read_only=True)

    class Meta:
        model = Notice
        fields = "__all__"
        read_only_fields = ["created_by", "publish_time"]


class EvaluationSerializer(serializers.ModelSerializer):
    """活动评价序列化器。"""
    activity_title = serializers.CharField(source="activity.title", read_only=True)
    volunteer_name = serializers.CharField(source="volunteer.real_name", read_only=True)

    class Meta:
        model = Evaluation
        fields = "__all__"
        read_only_fields = ["volunteer", "created_at"]

    def validate_rating(self, value):
        # 评分采用 1~5 的离散整数区间。
        if value < 1 or value > 5:
            raise serializers.ValidationError("评分范围为1-5")
        return value


class ActivityCommentSerializer(serializers.ModelSerializer):
    """活动评论序列化器。"""
    author_name = serializers.SerializerMethodField()
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_role = serializers.CharField(source="author.role", read_only=True)
    author_avatar = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent_author_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityComment
        fields = [
            "id",
            "activity",
            "author",
            "author_name",
            "author_username",
            "author_role",
            "author_avatar",
            "parent",
            "parent_author_name",
            "content",
            "is_deleted",
            "can_delete",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "is_deleted", "can_delete", "created_at", "updated_at"]

    def get_author_name(self, obj):
        return obj.author.real_name or obj.author.username

    def get_author_avatar(self, obj):
        if not obj.author.avatar:
            return None
        request = self.context.get("request")
        url = obj.author.avatar.url
        if request:
            try:
                return request.build_absolute_uri(url)
            except DisallowedHost:
                return url
        return url

    def get_parent_author_name(self, obj):
        if not obj.parent:
            return None
        return obj.parent.author.real_name or obj.parent.author.username

    def get_can_delete(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if obj.is_deleted:
            return False
        user = request.user
        return user.role == "system_admin" or obj.author_id == user.id

    def validate(self, attrs):
        # 更新场景下也要校验 parent 与 activity 的一致性。
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        activity = attrs.get("activity", getattr(self.instance, "activity", None))
        content = attrs.get("content")

        if content is not None:
            cleaned = content.strip()
            if not cleaned:
                raise serializers.ValidationError("评论内容不能为空")
            attrs["content"] = cleaned

        if parent and activity and parent.activity_id != activity.id:
            raise serializers.ValidationError("回复评论必须属于同一个活动")
        return attrs

    def to_representation(self, instance):
        # 软删除评论统一回显占位文案。
        data = super().to_representation(instance)
        if instance.is_deleted:
            data["content"] = "[该评论已删除]"
            data["can_delete"] = False
        return data


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器。"""
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = OperationLog
        fields = "__all__"

    def get_operator_name(self, obj):
        if obj.operator:
            return obj.operator.real_name or obj.operator.username
        return obj.operator_display









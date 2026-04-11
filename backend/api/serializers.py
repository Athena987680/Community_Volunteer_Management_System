from django.core.exceptions import DisallowedHost
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import User, Community, ActivityType, Activity, Registration, Attendance, Notice, Evaluation, ActivityComment

DECIMAL_ZERO = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))


class UserSerializer(serializers.ModelSerializer):
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
        if obj.role != "volunteer":
            return None
        agg = Attendance.objects.filter(
            registration__volunteer=obj,
            status="confirmed",
        ).aggregate(total=Coalesce(Sum("approved_hours"), DECIMAL_ZERO))
        return float(agg["total"]) if agg["total"] is not None else 0

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
    class Meta:
        model = User
        fields = ["real_name", "gender", "phone", "age", "community", "skills", "avatar"]

    def validate_phone(self, value):
        if value in ["", None]:
            return None
        return value


class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = "__all__"


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class ActivitySerializer(serializers.ModelSerializer):
    community_name = serializers.CharField(source="community.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.real_name", read_only=True)
    reviewer_name = serializers.CharField(source="reviewer.real_name", read_only=True)
    approved_count = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = "__all__"
        read_only_fields = ["created_by", "reviewer", "reviewed_at", "created_at", "updated_at"]

    def get_approved_count(self, obj):
        return obj.registrations.filter(status="approved").count()

    def get_type_display(self, obj):
        if obj.type == "其他" and obj.other_type:
            return f"其他（{obj.other_type}）"
        return obj.type

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        deadline = attrs.get("deadline", getattr(self.instance, "deadline", None))
        activity_type = attrs.get("type", getattr(self.instance, "type", None))
        other_type = attrs.get("other_type", getattr(self.instance, "other_type", None))

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("结束时间必须晚于开始时间")
        if deadline and start_time and deadline > start_time:
            raise serializers.ValidationError("报名截止时间不能晚于活动开始时间")

        if not activity_type:
            raise serializers.ValidationError("请选择活动类型")

        if activity_type == "其他":
            other_type_text = (other_type or "").strip()
            if not other_type_text:
                raise serializers.ValidationError("选择“其他”时必须填写类型补充")
            attrs["other_type"] = other_type_text
        else:
            active_types = set(ActivityType.objects.filter(is_active=True).values_list("name", flat=True))
            unchanged_existing_type = bool(self.instance and activity_type == self.instance.type)
            if activity_type not in active_types and not unchanged_existing_type:
                raise serializers.ValidationError("活动类型必须从系统预设类型中选择")
            attrs["other_type"] = None
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
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


class NoticeSerializer(serializers.ModelSerializer):
    community_name = serializers.CharField(source="community.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.real_name", read_only=True)

    class Meta:
        model = Notice
        fields = "__all__"
        read_only_fields = ["created_by", "publish_time"]


class EvaluationSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source="activity.title", read_only=True)
    volunteer_name = serializers.CharField(source="volunteer.real_name", read_only=True)

    class Meta:
        model = Evaluation
        fields = "__all__"
        read_only_fields = ["volunteer", "created_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("评分范围为1-5")
        return value


class ActivityCommentSerializer(serializers.ModelSerializer):
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
        data = super().to_representation(instance)
        if instance.is_deleted:
            data["content"] = "[该评论已删除]"
            data["can_delete"] = False
        return data






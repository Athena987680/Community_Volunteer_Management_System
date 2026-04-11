from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ("volunteer", "志愿者"),
        ("community_admin", "社区管理员"),
        ("system_admin", "系统管理员"),
    ]
    GENDER_CHOICES = [
        ("male", "男"),
        ("female", "女"),
    ]
    APPROVAL_CHOICES = [
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
    ]

    real_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="真实姓名")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="性别")
    phone = models.CharField(max_length=11, unique=True, null=True, blank=True, verbose_name="手机号")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="年龄")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True, verbose_name="头像")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="volunteer", verbose_name="角色")
    community = models.ForeignKey(
        "Community",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="所属社区",
    )
    skills = models.TextField(null=True, blank=True, verbose_name="技能特长")
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default="approved",
        verbose_name="角色审核状态",
    )
    approval_note = models.TextField(null=True, blank=True, verbose_name="角色审核备注")
    profile_completed = models.BooleanField(default=False, verbose_name="是否已完善资料")

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name


class Community(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="社区名称")
    description = models.TextField(null=True, blank=True, verbose_name="社区描述")
    cover_image = models.ImageField(upload_to="communities/", null=True, blank=True, verbose_name="封面图片")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "community"
        verbose_name = "社区"
        verbose_name_plural = verbose_name
        ordering = ["id"]


class ActivityType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="类型名称")
    sort_order = models.PositiveIntegerField(default=100, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    description = models.CharField(max_length=200, null=True, blank=True, verbose_name="说明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "activity_type"
        verbose_name = "活动类型"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "id"]


class Activity(models.Model):
    STATUS_CHOICES = [
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
        ("ongoing", "进行中"),
        ("finished", "已结束"),
    ]

    title = models.CharField(max_length=200, verbose_name="活动名称")
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.PROTECT,
        related_name="activities",
        verbose_name="活动类型",
    )
    other_type = models.CharField(max_length=80, null=True, blank=True, verbose_name="其他类型补充")
    location = models.CharField(max_length=200, verbose_name="活动地点")
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    max_volunteers = models.PositiveIntegerField(verbose_name="招募人数")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="activities", verbose_name="发起社区")
    description = models.TextField(verbose_name="活动描述")
    deadline = models.DateTimeField(verbose_name="报名截止时间")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="进行状态")
    allow_external = models.BooleanField(default=False, verbose_name="是否允许非本社区志愿者参与")
    cover_image = models.ImageField(upload_to="activities/", null=True, blank=True, verbose_name="封面图片")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_activities", verbose_name="创建人")
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_activities",
        verbose_name="审核人",
    )
    review_note = models.TextField(null=True, blank=True, verbose_name="审核备注")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "activity"
        verbose_name = "志愿活动"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "community", "start_time"], name="idx_activity_scope"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="ck_activity_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(deadline__lte=models.F("start_time")),
                name="ck_activity_deadline_before_start",
            ),
        ]


class Registration(models.Model):
    STATUS_CHOICES = [
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
        ("canceled", "已取消"),
    ]

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="registrations", verbose_name="活动")
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registrations", verbose_name="志愿者")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态")
    apply_time = models.DateTimeField(auto_now_add=True, verbose_name="报名时间")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_registrations",
        verbose_name="审核人",
    )
    review_note = models.TextField(null=True, blank=True, verbose_name="审核备注")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")

    class Meta:
        db_table = "registration"
        verbose_name = "报名记录"
        verbose_name_plural = verbose_name
        unique_together = ["activity", "volunteer"]
        ordering = ["-apply_time"]
        indexes = [
            models.Index(fields=["activity", "status"], name="idx_reg_activity_status"),
            models.Index(fields=["volunteer", "status"], name="idx_reg_vol_status"),
        ]


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("pending", "待审核"),
        ("confirmed", "已确认"),
        ("rejected", "已拒绝"),
    ]

    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name="attendance", verbose_name="报名记录")
    check_in_time = models.DateTimeField(null=True, blank=True, verbose_name="签到时间")
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name="签退时间")
    hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="原始工时")
    approved_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="确认工时")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="工时审核状态")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_attendances",
        verbose_name="审核人",
    )
    review_note = models.TextField(null=True, blank=True, verbose_name="审核备注")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")

    class Meta:
        db_table = "attendance"
        verbose_name = "签到与服务时长记录"
        verbose_name_plural = verbose_name
        ordering = ["-registration__apply_time"]
        indexes = [
            models.Index(fields=["status", "reviewed_at"], name="idx_att_status_reviewed"),
        ]


class Notice(models.Model):
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notices",
        verbose_name="所属社区(为空表示全局公告)",
    )
    publish_time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notices", verbose_name="发布人")

    class Meta:
        db_table = "notice"
        verbose_name = "公告"
        verbose_name_plural = verbose_name
        ordering = ["-publish_time"]


class Evaluation(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="evaluations", verbose_name="活动")
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluations", verbose_name="志愿者")
    rating = models.IntegerField(verbose_name="评分")
    comment = models.TextField(null=True, blank=True, verbose_name="评价内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评价时间")

    class Meta:
        db_table = "evaluation"
        verbose_name = "评价"
        verbose_name_plural = verbose_name
        unique_together = ["activity", "volunteer"]
        ordering = ["-created_at"]


class ActivityComment(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="comments", verbose_name="活动")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_comments", verbose_name="发布者")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="父评论",
    )
    content = models.TextField(verbose_name="评论内容")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "activity_comment"
        verbose_name = "活动评论"
        verbose_name_plural = verbose_name
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["activity", "created_at"], name="idx_comment_activity_time"),
            models.Index(fields=["activity", "parent"], name="idx_comment_activity_parent"),
            models.Index(fields=["activity", "is_deleted"], name="idx_comment_activity_del"),
        ]

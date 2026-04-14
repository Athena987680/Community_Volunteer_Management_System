"""核心业务数据模型定义。"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """系统用户模型，扩展框架默认用户字段。"""
    # 系统角色：决定可访问的页面与接口权限范围。
    ROLE_CHOICES = [
        ("volunteer", "志愿者"),
        ("community_admin", "社区管理员"),
        ("system_admin", "系统管理员"),
    ]
    # 基础档案字段枚举。
    GENDER_CHOICES = [
        ("male", "男"),
        ("female", "女"),
    ]
    # 社区管理员账号审核状态。
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
    """社区基础信息模型。"""
    name = models.CharField(max_length=100, unique=True, verbose_name="社区名称")
    description = models.TextField(null=True, blank=True, verbose_name="社区描述")
    cover_image = models.ImageField(upload_to="communities/", null=True, blank=True, verbose_name="封面图片")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "community"
        verbose_name = "社区"
        verbose_name_plural = verbose_name
        ordering = ["id"]


class CommunityChangeRequest(models.Model):
    """志愿者社区变更申请模型。"""
    # 申请审核状态（系统管理员处理）。
    STATUS_CHOICES = [
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
    ]

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_change_requests", verbose_name="申请人")
    from_community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_change_from_requests",
        verbose_name="原社区",
    )
    to_community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="community_change_to_requests",
        verbose_name="目标社区",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="审核状态")
    reason = models.TextField(null=True, blank=True, verbose_name="申请原因")
    review_note = models.TextField(null=True, blank=True, verbose_name="审核备注")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_community_change_requests",
        verbose_name="审核人",
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")

    class Meta:
        db_table = "community_change_request"
        verbose_name = "社区变更申请"
        verbose_name_plural = verbose_name
        ordering = ["-applied_at"]
        # 常用查询维度索引：按状态与申请人快速检索。
        indexes = [
            models.Index(fields=["status", "applied_at"], name="idx_ccr_status_applied"),
            models.Index(fields=["applicant", "status"], name="idx_ccr_applicant_status"),
        ]
        # 约束：同一志愿者同一时间只能有一条待审核申请。
        constraints = [
            models.UniqueConstraint(
                fields=["applicant"],
                condition=models.Q(status="pending"),
                name="uq_ccr_one_pending_per_user",
            ),
        ]


class ActivityType(models.Model):
    """活动类型字典模型。"""
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
    """志愿活动模型，包含审核与生命周期状态。"""
    # 审核状态：由系统管理员进行审批。
    REVIEW_STATUS_CHOICES = [
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
    ]
    # 生命周期状态：由时间推导 + 管理员操作共同驱动。
    STATUS_CHOICES = [
        ("unopened", "未开放"),
        ("recruiting", "报名中"),
        ("upcoming", "待开始"),
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
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default="pending", verbose_name="审核状态")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unopened", verbose_name="活动状态")
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
        # 活动查询核心索引（审核态+生命周期+社区+时间）。
        indexes = [
            models.Index(fields=["review_status", "status", "community", "start_time"], name="idx_activity_scope"),
        ]
        # 时间一致性约束。
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
    """志愿者报名记录模型。"""
    # 报名状态由审核流程驱动。
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
    """签到、签退及工时审核模型。"""
    # 工时审核状态：管理员确认/驳回。
    STATUS_CHOICES = [
        ("pending", "待审核"),
        ("confirmed", "已确认"),
        ("rejected", "已拒绝"),
    ]

    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name="attendance", verbose_name="报名记录")
    check_in_time = models.DateTimeField(null=True, blank=True, verbose_name="签到时间")
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name="签退时间")
    hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name="原始工时")
    approved_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name="确认工时")
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
    """公告模型，支持全局公告与社区公告。"""
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
    """活动评价模型。"""
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
    """活动评论模型，支持回复与软删除。"""
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
        # 评论区常用查询索引：按活动、时间、父评论和删除状态。
        indexes = [
            models.Index(fields=["activity", "created_at"], name="idx_comment_activity_time"),
            models.Index(fields=["activity", "parent"], name="idx_comment_activity_parent"),
            models.Index(fields=["activity", "is_deleted"], name="idx_comment_activity_del"),
        ]


class OperationLog(models.Model):
    """系统管理员操作审计日志模型。"""
    # 审计结果状态。
    STATUS_CHOICES = [
        ("success", "成功"),
        ("failed", "失败"),
    ]

    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operation_logs",
        verbose_name="操作人",
    )
    operator_display = models.CharField(max_length=100, null=True, blank=True, verbose_name="操作人显示名")
    module = models.CharField(max_length=80, verbose_name="模块")
    action = models.CharField(max_length=80, verbose_name="操作")
    method = models.CharField(max_length=10, verbose_name="请求方法")
    path = models.CharField(max_length=300, verbose_name="请求路径")
    target_type = models.CharField(max_length=80, null=True, blank=True, verbose_name="目标类型")
    target_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="目标ID")
    target_display = models.CharField(max_length=200, null=True, blank=True, verbose_name="目标描述")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="success", verbose_name="执行状态")
    status_code = models.PositiveSmallIntegerField(verbose_name="HTTP状态码")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    detail = models.TextField(null=True, blank=True, verbose_name="详细信息")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        # 支撑管理端多条件筛选的索引。
        indexes = [
            models.Index(fields=["created_at"], name="idx_oplog_created"),
            models.Index(fields=["operator", "created_at"], name="idx_oplog_operator_created"),
            models.Index(fields=["module", "action", "created_at"], name="idx_oplog_mod_act_created"),
            models.Index(fields=["status", "created_at"], name="idx_oplog_status_created"),
        ]




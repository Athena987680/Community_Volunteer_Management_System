# 迁移文件自动生成（历史信息保留在版本控制中）

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_activity_review_status_and_lifecycle_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunityChangeRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "待审核"),
                            ("approved", "已通过"),
                            ("rejected", "已拒绝"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="审核状态",
                    ),
                ),
                (
                    "reason",
                    models.TextField(blank=True, null=True, verbose_name="申请原因"),
                ),
                (
                    "review_note",
                    models.TextField(blank=True, null=True, verbose_name="审核备注"),
                ),
                (
                    "applied_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="申请时间"),
                ),
                (
                    "reviewed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="审核时间"
                    ),
                ),
                (
                    "effective_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="生效时间"
                    ),
                ),
                (
                    "applicant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="community_change_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="申请人",
                    ),
                ),
                (
                    "from_community",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="community_change_from_requests",
                        to="api.community",
                        verbose_name="原社区",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_community_change_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="审核人",
                    ),
                ),
                (
                    "to_community",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="community_change_to_requests",
                        to="api.community",
                        verbose_name="目标社区",
                    ),
                ),
            ],
            options={
                "verbose_name": "社区变更申请",
                "verbose_name_plural": "社区变更申请",
                "db_table": "community_change_request",
                "ordering": ["-applied_at"],
                "indexes": [
                    models.Index(
                        fields=["status", "applied_at"], name="idx_ccr_status_applied"
                    ),
                    models.Index(
                        fields=["applicant", "status"], name="idx_ccr_applicant_status"
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("status", "pending")),
                        fields=("applicant",),
                        name="uq_ccr_one_pending_per_user",
                    )
                ],
            },
        ),
    ]

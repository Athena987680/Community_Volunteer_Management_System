# 迁移文件自动生成（历史信息保留在版本控制中）

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_remove_communitychangerequest_effective_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationLog",
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
                    "operator_display",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="操作人显示名",
                    ),
                ),
                ("module", models.CharField(max_length=80, verbose_name="模块")),
                ("action", models.CharField(max_length=80, verbose_name="操作")),
                ("method", models.CharField(max_length=10, verbose_name="请求方法")),
                ("path", models.CharField(max_length=300, verbose_name="请求路径")),
                (
                    "target_type",
                    models.CharField(
                        blank=True, max_length=80, null=True, verbose_name="目标类型"
                    ),
                ),
                (
                    "target_id",
                    models.PositiveBigIntegerField(
                        blank=True, null=True, verbose_name="目标ID"
                    ),
                ),
                (
                    "target_display",
                    models.CharField(
                        blank=True, max_length=200, null=True, verbose_name="目标描述"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("success", "成功"), ("failed", "失败")],
                        default="success",
                        max_length=20,
                        verbose_name="执行状态",
                    ),
                ),
                (
                    "status_code",
                    models.PositiveSmallIntegerField(verbose_name="HTTP状态码"),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True, null=True, verbose_name="IP地址"
                    ),
                ),
                (
                    "detail",
                    models.TextField(blank=True, null=True, verbose_name="详细信息"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="operation_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="操作人",
                    ),
                ),
            ],
            options={
                "verbose_name": "操作日志",
                "verbose_name_plural": "操作日志",
                "db_table": "operation_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["created_at"], name="idx_oplog_created"),
                    models.Index(
                        fields=["operator", "created_at"],
                        name="idx_oplog_operator_created",
                    ),
                    models.Index(
                        fields=["module", "action", "created_at"],
                        name="idx_oplog_mod_act_created",
                    ),
                    models.Index(
                        fields=["status", "created_at"], name="idx_oplog_status_created"
                    ),
                ],
            },
        ),
    ]

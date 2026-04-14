# 迁移文件自动生成（历史信息保留在版本控制中）

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_seed_activity_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityComment",
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
                ("content", models.TextField(verbose_name="评论内容")),
                (
                    "is_deleted",
                    models.BooleanField(default=False, verbose_name="是否删除"),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="删除时间"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "activity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="api.activity",
                        verbose_name="活动",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activity_comments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="发布者",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="replies",
                        to="api.activitycomment",
                        verbose_name="父评论",
                    ),
                ),
            ],
            options={
                "verbose_name": "活动评论",
                "verbose_name_plural": "活动评论",
                "db_table": "activity_comment",
                "ordering": ["created_at", "id"],
            },
        ),
    ]

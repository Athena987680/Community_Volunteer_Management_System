# 迁移文件自动生成（历史信息保留在版本控制中）

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="activity",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "志愿活动",
                "verbose_name_plural": "志愿活动",
            },
        ),
        migrations.AlterModelOptions(
            name="attendance",
            options={
                "ordering": ["-registration__apply_time"],
                "verbose_name": "签到与服务时长记录",
                "verbose_name_plural": "签到与服务时长记录",
            },
        ),
        migrations.AlterModelOptions(
            name="community",
            options={
                "ordering": ["id"],
                "verbose_name": "社区",
                "verbose_name_plural": "社区",
            },
        ),
        migrations.AlterModelOptions(
            name="evaluation",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "评价",
                "verbose_name_plural": "评价",
            },
        ),
        migrations.AlterModelOptions(
            name="notice",
            options={
                "ordering": ["-publish_time"],
                "verbose_name": "公告",
                "verbose_name_plural": "公告",
            },
        ),
        migrations.AlterModelOptions(
            name="registration",
            options={
                "ordering": ["-apply_time"],
                "verbose_name": "报名记录",
                "verbose_name_plural": "报名记录",
            },
        ),
        migrations.AddField(
            model_name="activity",
            name="review_note",
            field=models.TextField(blank=True, null=True, verbose_name="审核备注"),
        ),
        migrations.AddField(
            model_name="activity",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="审核时间"),
        ),
        migrations.AddField(
            model_name="activity",
            name="reviewer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_activities",
                to=settings.AUTH_USER_MODEL,
                verbose_name="审核人",
            ),
        ),
        migrations.AddField(
            model_name="activity",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="更新时间"),
        ),
        migrations.AddField(
            model_name="attendance",
            name="approved_hours",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                verbose_name="确认工时",
            ),
        ),
        migrations.AddField(
            model_name="attendance",
            name="review_note",
            field=models.TextField(blank=True, null=True, verbose_name="审核备注"),
        ),
        migrations.AddField(
            model_name="attendance",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="审核时间"),
        ),
        migrations.AddField(
            model_name="attendance",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_attendances",
                to=settings.AUTH_USER_MODEL,
                verbose_name="审核人",
            ),
        ),
        migrations.AddField(
            model_name="registration",
            name="review_note",
            field=models.TextField(blank=True, null=True, verbose_name="审核备注"),
        ),
        migrations.AddField(
            model_name="registration",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="审核时间"),
        ),
        migrations.AddField(
            model_name="registration",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_registrations",
                to=settings.AUTH_USER_MODEL,
                verbose_name="审核人",
            ),
        ),
        migrations.AlterField(
            model_name="activity",
            name="max_volunteers",
            field=models.PositiveIntegerField(verbose_name="招募人数"),
        ),
        migrations.AlterField(
            model_name="activity",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "待审核"),
                    ("approved", "已通过"),
                    ("rejected", "已拒绝"),
                    ("ongoing", "进行中"),
                    ("finished", "已结束"),
                ],
                default="pending",
                max_length=20,
                verbose_name="进行状态",
            ),
        ),
        migrations.AlterField(
            model_name="attendance",
            name="hours",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                verbose_name="原始工时",
            ),
        ),
        migrations.AlterField(
            model_name="attendance",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "待审核"),
                    ("confirmed", "已确认"),
                    ("rejected", "已拒绝"),
                ],
                default="pending",
                max_length=20,
                verbose_name="工时审核状态",
            ),
        ),
        migrations.AlterField(
            model_name="notice",
            name="community",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notices",
                to="api.community",
                verbose_name="所属社区(为空表示全局公告)",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "待审核"),
                    ("approved", "已通过"),
                    ("rejected", "已拒绝"),
                    ("canceled", "已取消"),
                ],
                default="pending",
                max_length=20,
                verbose_name="状态",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="age",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="年龄"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="evaluation",
            unique_together={("activity", "volunteer")},
        ),
    ]

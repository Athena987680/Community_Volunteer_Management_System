# 迁移文件自动生成（历史信息保留在版本控制中）

import django.db.models.deletion
from django.db import migrations, models


def copy_activity_type_to_fk(apps, schema_editor):
    Activity = apps.get_model("api", "Activity")
    ActivityType = apps.get_model("api", "ActivityType")

    fallback_type, _ = ActivityType.objects.get_or_create(
        name="其他",
        defaults={
            "sort_order": 9999,
            "is_active": True,
            "description": "迁移兜底类型",
        },
    )

    for activity in Activity.objects.all().only("id", "type", "other_type", "activity_type"):
        type_name = (activity.type or "").strip()
        if not type_name:
            type_name = "其他"

        target_type, _ = ActivityType.objects.get_or_create(
            name=type_name,
            defaults={
                "sort_order": 9999,
                "is_active": True,
                "description": "历史活动类型自动补齐",
            },
        )
        activity.activity_type_id = target_type.id if target_type else fallback_type.id
        activity.save(update_fields=["activity_type"])


def rollback_fk_to_text(apps, schema_editor):
    Activity = apps.get_model("api", "Activity")
    for activity in Activity.objects.select_related("activity_type").all():
        activity.type = activity.activity_type.name if activity.activity_type else "其他"
        activity.save(update_fields=["type"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_activitycomment"),
    ]

    operations = [
        migrations.AddField(
            model_name="activity",
            name="activity_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="activities",
                to="api.activitytype",
                verbose_name="活动类型",
            ),
        ),
        migrations.RunPython(copy_activity_type_to_fk, rollback_fk_to_text),
        migrations.AlterField(
            model_name="activity",
            name="activity_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="activities",
                to="api.activitytype",
                verbose_name="活动类型",
            ),
        ),
        migrations.RemoveField(
            model_name="activity",
            name="type",
        ),
        migrations.AddIndex(
            model_name="activity",
            index=models.Index(fields=["status", "community", "start_time"], name="idx_activity_scope"),
        ),
        migrations.AddIndex(
            model_name="activitycomment",
            index=models.Index(fields=["activity", "created_at"], name="idx_comment_activity_time"),
        ),
        migrations.AddIndex(
            model_name="activitycomment",
            index=models.Index(fields=["activity", "parent"], name="idx_comment_activity_parent"),
        ),
        migrations.AddIndex(
            model_name="activitycomment",
            index=models.Index(fields=["activity", "is_deleted"], name="idx_comment_activity_del"),
        ),
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(fields=["status", "reviewed_at"], name="idx_att_status_reviewed"),
        ),
        migrations.AddIndex(
            model_name="registration",
            index=models.Index(fields=["activity", "status"], name="idx_reg_activity_status"),
        ),
        migrations.AddIndex(
            model_name="registration",
            index=models.Index(fields=["volunteer", "status"], name="idx_reg_vol_status"),
        ),
        migrations.AddConstraint(
            model_name="activity",
            constraint=models.CheckConstraint(
                condition=models.Q(("end_time__gt", models.F("start_time"))),
                name="ck_activity_end_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="activity",
            constraint=models.CheckConstraint(
                condition=models.Q(("deadline__lte", models.F("start_time"))),
                name="ck_activity_deadline_before_start",
            ),
        ),
    ]

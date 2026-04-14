from django.db import migrations, models
from django.utils import timezone


def _derive_status(activity, now):
    if now >= activity.end_time:
        return "finished"
    if now >= activity.start_time:
        return "ongoing"
    if now > activity.deadline:
        return "upcoming"
    return "recruiting"


def migrate_activity_statuses(apps, schema_editor):
    Activity = apps.get_model("api", "Activity")
    now = timezone.now()
    for activity in Activity.objects.all().only("id", "status", "start_time", "end_time", "deadline"):
        old_status = activity.status
        if old_status == "pending":
            activity.review_status = "pending"
            activity.status = "unopened"
        elif old_status == "rejected":
            activity.review_status = "rejected"
            activity.status = "unopened"
        elif old_status == "finished":
            activity.review_status = "approved"
            activity.status = "finished"
        elif old_status == "ongoing":
            activity.review_status = "approved"
            activity.status = "ongoing"
        elif old_status == "approved":
            activity.review_status = "approved"
            activity.status = _derive_status(activity, now)
        else:
            activity.review_status = "pending"
            activity.status = "unopened"
        activity.save(update_fields=["review_status", "status"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_attendance_hours_one_decimal"),
    ]

    operations = [
        migrations.AddField(
            model_name="activity",
            name="review_status",
            field=models.CharField(
                choices=[("pending", "待审核"), ("approved", "已通过"), ("rejected", "已拒绝")],
                default="pending",
                max_length=20,
                verbose_name="审核状态",
            ),
        ),
        migrations.RunPython(migrate_activity_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="activity",
            name="status",
            field=models.CharField(
                choices=[
                    ("unopened", "未开放"),
                    ("recruiting", "报名中"),
                    ("upcoming", "待开始"),
                    ("ongoing", "进行中"),
                    ("finished", "已结束"),
                ],
                default="unopened",
                max_length=20,
                verbose_name="活动状态",
            ),
        ),
        migrations.RemoveIndex(
            model_name="activity",
            name="idx_activity_scope",
        ),
        migrations.AddIndex(
            model_name="activity",
            index=models.Index(
                fields=["review_status", "status", "community", "start_time"],
                name="idx_activity_scope",
            ),
        ),
    ]

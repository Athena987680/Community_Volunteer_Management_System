# 迁移文件自动生成（历史信息保留在版本控制中）

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_alter_activity_options_alter_attendance_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="approval_note",
            field=models.TextField(blank=True, null=True, verbose_name="角色审核备注"),
        ),
        migrations.AddField(
            model_name="user",
            name="approval_status",
            field=models.CharField(
                choices=[
                    ("pending", "待审核"),
                    ("approved", "已通过"),
                    ("rejected", "已拒绝"),
                ],
                default="approved",
                max_length=20,
                verbose_name="角色审核状态",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="profile_completed",
            field=models.BooleanField(default=False, verbose_name="是否已完善资料"),
        ),
        migrations.AlterField(
            model_name="user",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("male", "男"), ("female", "女")],
                max_length=10,
                null=True,
                verbose_name="性别",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(
                blank=True, max_length=11, null=True, unique=True, verbose_name="手机号"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="real_name",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="真实姓名"
            ),
        ),
    ]

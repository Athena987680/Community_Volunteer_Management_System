# 迁移文件自动生成（历史信息保留在版本控制中）

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_communitychangerequest"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="communitychangerequest",
            name="effective_at",
        ),
    ]

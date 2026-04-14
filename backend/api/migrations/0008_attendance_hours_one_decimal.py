from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models

HOUR_QUANT = Decimal("0.1")


def _round_hour(value):
    if value is None:
        return None
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return decimal_value.quantize(HOUR_QUANT, rounding=ROUND_HALF_UP)


def normalize_attendance_hours(apps, schema_editor):
    Attendance = apps.get_model("api", "Attendance")
    for item in Attendance.objects.all().only("id", "hours", "approved_hours"):
        new_hours = _round_hour(item.hours)
        new_approved = _round_hour(item.approved_hours)
        updates = []
        if new_hours != item.hours:
            item.hours = new_hours
            updates.append("hours")
        if new_approved != item.approved_hours:
            item.approved_hours = new_approved
            updates.append("approved_hours")
        if updates:
            item.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_activity_type_fk_constraints_indexes"),
    ]

    operations = [
        migrations.RunPython(normalize_attendance_hours, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="attendance",
            name="hours",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True, verbose_name="原始工时"),
        ),
        migrations.AlterField(
            model_name="attendance",
            name="approved_hours",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True, verbose_name="确认工时"),
        ),
    ]

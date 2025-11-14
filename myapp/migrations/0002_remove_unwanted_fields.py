from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),  # since you only have 0001_initial.py
    ]

    operations = [
        # Remove fields from NormalReservationTable
        migrations.RemoveField(
            model_name='normalreservationtable',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='normalreservationtable',
            name='date_updated',
        ),
        # Remove field from SessionDishHistory
        migrations.RemoveField(
            model_name='sessiondishhistory',
            name='timestamp',
        ),
    ]

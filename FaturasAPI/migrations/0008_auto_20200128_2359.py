# Generated by Django 3.0.2 on 2020-01-28 23:59

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FaturasAPI', '0007_auto_20200124_1236'),
    ]

    operations = [
        migrations.AddField(
            model_name='fatura',
            name='data_delete',
            field=models.DateField(default=datetime.date(2020, 2, 12)),
        ),
        migrations.AddField(
            model_name='fatura',
            name='is_garantia',
            field=models.BinaryField(default=False),
        ),
    ]
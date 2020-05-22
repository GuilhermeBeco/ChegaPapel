# Generated by Django 3.0.2 on 2020-01-23 11:32

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('FaturasAPI', '0005_auto_20200122_1316'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fatura',
            name='username',
        ),
        migrations.AddField(
            model_name='fatura',
            name='user',
            field=models.ForeignKey(default=8, on_delete=django.db.models.deletion.DO_NOTHING, to='FaturasAPI.UserFinal'),
        ),
        migrations.AlterField(
            model_name='fatura',
            name='pdf',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(location='/media/pdfs'), upload_to=''),
        ),
    ]

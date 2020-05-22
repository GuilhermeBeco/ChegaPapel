import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage


class UserFinal(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    nif = models.IntegerField(default='000000000')
    pass


# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/

fs = FileSystemStorage(location='media/pdfs')

DEFAULT_USER_ID = 8


class Fatura(models.Model):
    id = models.AutoField(primary_key=True)
    entidade = models.TextField(blank=False)
    valor = models.DecimalField(max_digits=9, decimal_places=2)
    pdf = models.FileField(storage=fs)
    data = models.DateField(auto_now_add=True)
    data_delete = models.DateField(default=datetime.date.today() + datetime.timedelta(days=15))
    url = models.TextField(blank=True)
    is_garantia = models.BinaryField(default=False)
    user = models.ForeignKey(UserFinal, on_delete=models.DO_NOTHING, default=DEFAULT_USER_ID)
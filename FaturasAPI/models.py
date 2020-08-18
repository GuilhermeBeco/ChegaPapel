import datetime

from django_hash_field import HashField
from hashid_field import HashidField
from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage


class SecurityQuestion(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.TextField(blank=False)


class UserFinal(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    nif = models.IntegerField(default='000000000')
    question = models.ManyToManyField(SecurityQuestion, through='SecurityQuestionsInter')
    pass


class SecurityQuestionsInter(models.Model):
    profile = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    security_questions = models.ForeignKey(SecurityQuestion, on_delete=models.DO_NOTHING)
    answer = models.TextField(blank=False,default="none")


fs = FileSystemStorage(location='media/pdfs')

DEFAULT_USER_ID = 8


class AdminEntidade(models.Model):
    id = models.AutoField(primary_key=True)
    userFinal = models.OneToOneField(UserFinal, on_delete=models.DO_NOTHING)
    cargo = models.TextField(blank=False)
    pass


class Entidade(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.TextField(blank=False)
    morada = models.TextField(blank=False)
    admin = models.ForeignKey(AdminEntidade, on_delete=models.DO_NOTHING)


class Funcionario(models.Model):
    id = models.AutoField(primary_key=True)
    userFinal = models.OneToOneField(UserFinal, on_delete=models.DO_NOTHING)
    entidade = models.ForeignKey(Entidade, on_delete=models.DO_NOTHING)
    pass


class Fatura(models.Model):
    id = models.AutoField(primary_key=True)
    entidade = models.ForeignKey(Entidade, on_delete=models.DO_NOTHING)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.DO_NOTHING)
    valor = models.DecimalField(max_digits=9, decimal_places=2)
    pdf = models.FileField(storage=fs)
    data = models.DateField(auto_now_add=True)
    # mudar o default para um auto now add + 15 days
    data_delete = models.DateField(default=datetime.date.today() + datetime.timedelta(days=15))
    url = models.TextField(blank=True)
    is_garantia = models.BinaryField(default=False)

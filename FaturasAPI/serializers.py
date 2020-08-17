from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from FaturasAPI.models import UserFinal, Fatura, Entidade, AdminEntidade, Funcionario
from rest_framework import serializers
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class UserSerializerDetails(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']


class UserSerializerDetailsTeste(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UserFinalSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = UserFinal
        fields = ['user', 'nif']


class UserFinalSerializerDetails(serializers.ModelSerializer):
    user = UserSerializerDetails(many=False)

    class Meta:
        model = UserFinal
        fields = ['user', 'nif']

    def create(self, validated_data):
        logger.error('Something went wrong!')
        nif = validated_data.pop('nif')
        userData = validated_data.pop("user")
        user = User.objects.create(**userData)
        user.set_password(userData.get('password'))
        user.save()
        userFinal = UserFinal.objects.create(user=user, nif=nif)
        return userFinal


class UserFinalSerializerDetailsTeste(serializers.ModelSerializer):
    user = UserSerializerDetailsTeste(many=False)

    class Meta:
        model = UserFinal
        fields = ['user', 'nif']

    def updateUser(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        logger.error(instance)
        return instance

    def update(self, instance, validated_data):
        userFinal = UserFinal.objects.get(pk=instance.id)
        userFinal.user = instance.user
        userFinal.nif = instance.nif
        userFinal.nif = validated_data.get('nif', instance.nif)
        userFinal.user = self.updateUser(User.objects.get(pk=instance.user.id), validated_data.get('user'))
        userFinal.save()
        logger.error(userFinal)
        return userFinal


class FaturaSerializer(serializers.ModelSerializer):
    user = UserFinalSerializer(many=False)

    class Meta:
        model = Fatura
        fields = ['id', 'entidade', 'valor', 'data', 'user', 'pdf', 'url']

    # def update(self, instance, validated_data):
    #     fatura = Fatura.objects.get(pk=instance.id)
    #     fatura.user = UserFinal.objects.get(pk=instance.user_id)
    #     fatura.save()
    #     logger.error(fatura)
    #     return fatura


class FaturaSerializerPost(serializers.ModelSerializer):
    class Meta:
        model = Fatura
        fields = ['entidade', 'valor', 'data', 'pdf']


# noinspection PyMethodOverriding
class EntidadeSerializerPost(serializers.ModelSerializer):
    class Meta:
        model = Entidade
        fields = ['nome', 'morada']

    def create(self, validated_data, email):
        entidade = Entidade()
        entidade.nome = validated_data.pop("nome")
        entidade.morada = validated_data.pop("morada")
        entidade.admin = AdminEntidade.objects.get(userFinal__user__email=email)
        entidade.save()


class EntidadeSerializerDetails(serializers.ModelSerializer):
    class Meta:
        model = Entidade
        fields = ['nome', 'morada', 'admin']


class AdminSerializer(serializers.ModelSerializer):
    userFinal = UserFinalSerializerDetails(many=False)

    class Meta:
        model = AdminEntidade
        fields = ['cargo', 'userFinal']

    def create(self, validated_data):
        ufSerializer = UserFinalSerializerDetails()
        uf = ufSerializer.create(validated_data=validated_data.pop("userFinal"))
        cargoCreate = validated_data.pop("cargo")
        return AdminEntidade.objects.create(userFinal=uf, cargo=cargoCreate)


class AdminSerializerDetails(serializers.ModelSerializer):
    userFinal = UserFinalSerializerDetailsTeste(many=False)

    class Meta:
        model = AdminEntidade
        fields = ['cargo', 'userFinal']

    def update(self, instance, validated_data):
        admin = AdminEntidade.objects.get(pk=instance.id)
        admin.cargo = instance.cargo
        ufSerializerDetailsTeste = UserFinalSerializerDetailsTeste()
        admin.userFinal = ufSerializerDetailsTeste.update(UserFinal.objects.get(pk=instance.userFinal.id),
                                                          validated_data.pop("userFinal"))
        admin.save()
        return admin


class FuncionarioSerializer(serializers.ModelSerializer):
    userFinal = UserFinalSerializerDetails(many=False)

    class Meta:
        model = Funcionario
        fields = ['userFinal']

    def create(self, validated_data, admin):
        ufSerializer = UserFinalSerializerDetails()
        uf = ufSerializer.create(validated_data=validated_data.pop("userFinal"))
        entidade = Entidade.objects.get(admin=admin)
        return Funcionario.objects.create(userFinal=uf, entidade=entidade)


class FuncionarioDetails(serializers.ModelSerializer):
    userFinal = UserFinalSerializerDetailsTeste(many=False)

    class Meta:
        model = Funcionario
        fields = ['userFinal']

    def update(self, instance, validated_data):
        funcionario = Funcionario.objects.get(pk=instance.id)
        ufSerializerDetailsTeste = UserFinalSerializerDetailsTeste()
        funcionario.userFinal = ufSerializerDetailsTeste.update(UserFinal.objects.get(pk=instance.userFinal.id),
                                                                validated_data.pop("userFinal"))
        funcionario.save()
        return funcionario


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

# On django views

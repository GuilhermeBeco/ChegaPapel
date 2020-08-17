import os
import datetime
import qrcode
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import Http404, QueryDict, HttpResponse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
import logging
from FaturasAPI.models import UserFinal, Fatura, AdminEntidade, Entidade, Funcionario
from FaturasAPI.serializers import UserFinalSerializer, UserFinalSerializerDetails, UserFinalSerializerDetailsTeste, \
    FaturaSerializer, FaturaSerializerPost, EntidadeSerializerPost, AdminSerializer, AdminSerializerDetails, \
    FuncionarioSerializer, FuncionarioDetails
from rest_framework.permissions import IsAuthenticated

from untitled import settings

logger = logging.getLogger(__name__)


class UserList(generics.GenericAPIView):
    serializer_class = UserFinalSerializerDetails
    queryset = UserFinal.objects.all()

    def get(self, request, format=None):
        users = UserFinal.objects.all()
        serializer = UserFinalSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializerUser = UserFinalSerializerDetails(data=request.data)
        if serializerUser.is_valid():
            serializerUser.save()
            return Response(serializerUser.data, status.HTTP_201_CREATED)
        return Response(serializerUser.errors, status.HTTP_400_BAD_REQUEST)


class UserListDetail(generics.GenericAPIView):
    serializer_class = UserFinalSerializerDetailsTeste
    queryset = UserFinal.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        try:
            return UserFinal.objects.get(user__email=pk)
        except UserFinal.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):

        serializer = UserFinalSerializerDetails(self.get_object(pk))
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        user = self.get_object(pk)
        data = QueryDict.copy(request.data)
        serializer = UserFinalSerializerDetailsTeste(user, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        userFinal = self.get_object(pk)
        user = userFinal.user
        if user.check_password(request.data['password_old']):
            if request.data['password'] == request.data['password_confirmation']:
                user.set_password(raw_password=request.data['password'])
                user.save()
                return Response(status=status.HTTP_202_ACCEPTED)
            else:
                return Response('The passwords don´t match', status=status.HTTP_400_BAD_REQUEST)
        return Response('The old password doesn´t match', status=status.HTTP_400_BAD_REQUEST)


class FaturaList(generics.GenericAPIView):
    queryset = Fatura.objects.all()

    def get(self, request, email, format=None):
        user = UserFinal.objects.get(user__email=email)
        faturas = Fatura.objects.all().filter(user=user)
        serializer = FaturaSerializer(faturas, many=True)
        return Response(serializer.data)


class FaturaListDetails(generics.GenericAPIView):
    queryset = Fatura.objects.all()

    def patch(self, request, pk, email, format=None):
        user = UserFinal.objects.get(user__email=email)
        try:
            faturas = Fatura.objects.filter(id=pk, user=user).get()
            if faturas.is_garantia:
                faturas.is_garantia = False
                faturas.data_delete = faturas.data + datetime.timedelta(days=15)
                faturas.save()
                return Response(status=status.HTTP_202_ACCEPTED)
            else:
                faturas.is_garantia = True
                if "extensao_garantia" in request.data and request.data["extensao_garantia"] > 0:
                    faturas.data_delete = faturas.data + relativedelta(years=2 + request.data["extensao_garantia"])
                else:
                    faturas.data_delete = faturas.data + relativedelta(years=2)
                faturas.save()
                return Response(status=status.HTTP_202_ACCEPTED)
        except:
            return Response("A fatura não existe ou não lhe corresponde",
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, email, format=None):
        logger.error(pk)
        faturas = Fatura.objects.filter(id=pk).get()
        user = UserFinal.objects.get(user__email=email)
        faturas.user = user
        faturas.save()
        return Response(status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, email, format=None):
        user = UserFinal.objects.get(user__email=email)
        faturas = Fatura.objects.filter(id=pk, user=user).get()
        if datetime.date.today() > faturas.data_delete:
            if os.path.exists("media/pdfs/" + faturas.pdf.name):
                os.remove("media/pdfs/" + faturas.pdf.name)
            else:
                print("The file does not exist")
            faturas.delete()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            if faturas.is_garantia:
                return Response("A sua garantia ainda não fez 2 anos para poder ser eliminada",
                                status=status.HTTP_400_BAD_REQUEST)
            return Response("A sua fatura ainda não fez 15 dias para poder ser eliminada",
                            status=status.HTTP_400_BAD_REQUEST)


class FaturasCreate(generics.GenericAPIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):
        is_qr = int(request.data.pop('qr')[0])
        serializerUser = FaturaSerializerPost(data=request.data)
        if serializerUser.is_valid():
            serializerUser.save()
            fatura = Fatura.objects.get(pdf=serializerUser.data.get('pdf'))
            logger.error('' + str(fatura.id) + ':' + fatura.pdf.name)
            fatura.url = 'http://127.0.0.1:8000/faturas/download/' + fatura.pdf.name
            fatura.save()
            if is_qr == 1:
                qr = qrcode.make(fatura.id)
                qr.save('media/qr/' + fatura.pdf.name + '.jpeg')
                try:
                    with open('media/qr/' + fatura.pdf.name + '.jpeg', "rb") as f:
                        return HttpResponse(f.read(), content_type="image/jpeg")
                except IOError:
                    return Response("Erro no QR", status.HTTP_400_BAD_REQUEST)
            return HttpResponse(fatura.id, status=status.HTTP_201_CREATED)
        return Response(serializerUser.errors, status.HTTP_400_BAD_REQUEST)


class AdminEntidadeView(generics.GenericAPIView):
    serializer_class = AdminSerializer

    def post(self, request, format=None):
        serializedAdmin = AdminSerializer(data=request.data)
        if serializedAdmin.is_valid():
            serializedAdmin.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializedAdmin.errors, status.HTTP_400_BAD_REQUEST)


class AdminEntidadeDetails(generics.GenericAPIView):
    serializer_class = AdminSerializerDetails
    permission_classes = (IsAuthenticated,)

    def get_object(self, email):
        try:
            return AdminEntidade.objects.get(userFinal__user__email=email)
        except UserFinal.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        serializer = AdminSerializerDetails(self.get_object(request.user.username))
        return Response(serializer.data)

    def put(self, request, format=None):
        admin = self.get_object(request.user.username)
        serializer = AdminSerializerDetails(admin, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        admin = self.get_object(request.user.username)
        user = admin.userFinal.user
        if user.check_password(request.data['password_old']):
            if request.data['password'] == request.data['password_confirmation']:
                user.set_password(raw_password=request.data['password'])
                user.save()
                return Response(status=status.HTTP_202_ACCEPTED)
            else:
                return Response('The passwords don´t match', status=status.HTTP_400_BAD_REQUEST)
        return Response('The old password doesn´t match', status=status.HTTP_400_BAD_REQUEST)


class EntidadePost(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        serializedEntidade = EntidadeSerializerPost(data=request.data)
        if serializedEntidade.is_valid() and AdminEntidade.objects.filter(userFinal__user__email
                                                                          =request.data.get("email")).exists():
            if AdminEntidade.objects.get(userFinal__user__email=request.data.get("email")).ativo != 0:
                serializedEntidade.create(serializedEntidade.data, request.data.get("email"))
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response("Your new admin is not active", status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializedEntidade.errors + " Or your admin does not exist", status.HTTP_400_BAD_REQUEST)


class EntidadeDetails(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        try:
            admin = AdminEntidade.objects.get(userFinal__user__username=request.user.username)
        except admin.DoesNotExist:
            return Response("You are not an admin", status.HTTP_400_BAD_REQUEST)
        if admin.userFinal.user.is_active == 0:
            return Response("You are an activated admin.", status.HTTP_400_BAD_REQUEST)
        if len(admin.entidade_set.all()) == 0:
            return Response("You aren't associated with any entity", status.HTTP_400_BAD_REQUEST)

        funcionarios = Funcionario.objects.filter(entidade=admin.entidade_set.first())
        serializer = FuncionarioDetails(funcionarios, many=True)
        return Response(serializer.data)

    def put(self, request, format=None):
        admin = AdminEntidade.objects.get(userFinal__user__username=request.user.username)
        entidade = Entidade.objects.get(admin=admin)
        serializedEntidade = EntidadeSerializerPost(entidade, request.data)
        if serializedEntidade.is_valid():
            serializedEntidade.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializedEntidade.errors, status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        logger.error(request.user.username)
        admin = AdminEntidade.objects.get(userFinal__user__username=request.user.username)
        entidade = Entidade.objects.get(admin=admin)
        if AdminEntidade.objects.filter(userFinal__user__email=request.data.get("newEmail")).exists():
            newAdmin = AdminEntidade.objects.get(userFinal__user__email=request.data.get("newEmail"))
            if newAdmin.userFinal.user.is_active != 0:
                entidade.admin = newAdmin
                entidade.save()
                admin.userFinal.user.is_active = 0
                # logger.error(admin.save())
                # Nao sei o porque de o admin, sendo uma sub sub classe de user nao da save ao authuser
                admin.userFinal.user.save()
                return Response(status=status.HTTP_202_ACCEPTED)
            else:
                return Response("Your new admin is not active", status.HTTP_400_BAD_REQUEST)
        else:
            return Response("Your new admin does not exist", status.HTTP_400_BAD_REQUEST)


class FuncionariosPost(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            admin = AdminEntidade.objects.get(userFinal__user__username=request.user.username)
        except admin.DoesNotExist:
            return Response("You are not an admin", status.HTTP_400_BAD_REQUEST)
        if admin.userFinal.user.is_active == 0:
            return Response("You are an activated admin.", status.HTTP_400_BAD_REQUEST)
        if len(admin.entidade_set.all()) == 0:
            return Response("You aren't associated with any entity", status.HTTP_400_BAD_REQUEST)
        serializedFuncionario = FuncionarioSerializer(data=request.data)
        if serializedFuncionario.is_valid():
            serializedFuncionario.create(serializedFuncionario.data, admin)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializedFuncionario.errors, status.HTTP_400_BAD_REQUEST)


class FuncionariosDetails(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    # only funcionario
    def put(self, request, format=None):
        try:
            funcionario = Funcionario.objects.get(userFinal__user__username=request.user.username)
        except funcionario.DoesNotExist:
            return Response("You are not a staff member", status.HTTP_400_BAD_REQUEST)
        if funcionario.userFinal.user.is_active == 0:
            return Response("You are an activated staff member.", status.HTTP_400_BAD_REQUEST)
        serializedFuncionario = FuncionarioDetails(data=request.data)
        if serializedFuncionario.is_valid():
            serializedFuncionario.update(funcionario, serializedFuncionario.data)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializedFuncionario.errors, status=status.HTTP_400_BAD_REQUEST)

    # only admin
    def patch(self, request, format=None):
        try:
            admin = AdminEntidade.objects.get(userFinal__user__username=request.user.username)
        except admin.DoesNotExist:
            return Response("You are not an admin", status.HTTP_400_BAD_REQUEST)
        if admin.userFinal.user.is_active == 0:
            return Response("You are an activated admin.", status.HTTP_400_BAD_REQUEST)
        if len(admin.entidade_set.all()) == 0:
            return Response("You aren't associated with any entity", status.HTTP_400_BAD_REQUEST)
        funcionario = Funcionario.objects.get(userFinal__user__email=request.data.get("email"))
        if funcionario.entidade_id == admin.entidade_set.first().id:
            funcionario.userFinal.user.is_active = 0
            funcionario.userFinal.user.save()
            # Nao sei o porque de o funcionario, sendo uma sub sub classe de user nao da save ao authuser
            # funcionario.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response("This staff member is not associated with your entity", status.HTTP_400_BAD_REQUEST)


class Activation(generics.GenericAPIView):
    def post(self, request, format=None):
        if not AdminEntidade.objects.filter(userFinal__user__email=request.data.get("email")).exists():
            return Response("Your admin does not exist", status.HTTP_400_BAD_REQUEST)
        admin = AdminEntidade.objects.get(userFinal__user__email=request.data.get("email"))
        logger.error(admin.cargo)
        if admin.userFinal.user.is_active == 0:
            current_site = get_current_site(request)
            subject = 'Ativate your account'
            uid = urlsafe_base64_encode(force_bytes(admin.userFinal.user.email)).decode()

            # activation_link = "{0}/uid={1}/token={2}".format(current_site, uid, token)
            activation_link = "{0}/activate/{1}/".format(current_site, uid)

            email_from = settings.EMAIL_HOST_USER
            to_email = [admin.userFinal.user.email]
            message = "Hello {0},\n {1}".format(admin.userFinal.user.username, activation_link)
            send_mail(subject, message, email_from, to_email)
            return Response('Please confirm your email address to complete the registration')
        else:
            return Response("Your admin is already active", status=status.HTTP_202_ACCEPTED)


class ReActivate(generics.GenericAPIView):
    def get(self, request, uidb64):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            admin = User.objects.get(email=uid)
        except (TypeError, ValueError, OverflowError, admin.DoesNotExist):
            admin = None

        if admin is not None:
            admin.is_active = 1
            admin.save()
            return Response('Account activated successfully', status.HTTP_202_ACCEPTED)
        else:
            return Response("Your new admin does not exist", status.HTTP_400_BAD_REQUEST)


def download_file(request, filepath, format=None):
    fl_path = 'media/pdfs/'
    filename = filepath

    fl = open(fl_path + filename + '.pdf', 'rb')
    mime_type = '.pdf'
    response = HttpResponse(fl, content_type=mime_type)
    response["Content-Disposition"] = "attachment; filename=%s" % filename
    return response

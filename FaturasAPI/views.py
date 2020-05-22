import os
import datetime
import qrcode
from dateutil.relativedelta import relativedelta
from django.http import Http404, QueryDict, HttpResponse
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
import logging
from FaturasAPI.models import UserFinal, Fatura
from FaturasAPI.serializers import UserFinalSerializer, UserFinalSerializerDetails, UserFinalSerializerDetailsTeste, \
    FaturaSerializer, FaturaSerializerPost

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

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
            if is_qr==1:
                qr = qrcode.make(fatura.id)
                qr.save('media/qr/' + fatura.pdf.name + '.jpeg')
                try:
                    with open('media/qr/' + fatura.pdf.name + '.jpeg', "rb") as f:
                        return HttpResponse(f.read(), content_type="image/jpeg")
                except IOError:
                    return Response("Erro no QR", status.HTTP_400_BAD_REQUEST)
            return HttpResponse(fatura.id, status=status.HTTP_201_CREATED)
        return Response(serializerUser.errors, status.HTTP_400_BAD_REQUEST)


def download_file(request, filepath, format=None):
    fl_path = 'media/pdfs/'
    filename = filepath

    fl = open(fl_path + filename + '.pdf', 'rb')
    mime_type = '.pdf'
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

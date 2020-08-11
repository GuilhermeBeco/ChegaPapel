"""untitled URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from FaturasAPI import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('users/', views.UserList.as_view()),
    path('users/<str:pk>/', views.UserListDetail.as_view()),
    path('faturas/', views.FaturasCreate.as_view()),
    path('faturas/<str:email>/', views.FaturaList.as_view()),
    path('faturas/<str:email>/<int:pk>/', views.FaturaListDetails.as_view()),
    path('faturas/download/<str:filepath>/', views.download_file),
    path('api/login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('entidades/', views.Entidade.as_view()),
    path('adminEntidade/',views.AdminEntidade.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)

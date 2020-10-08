from django.urls import path, include
from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'Encuesta', views.EncuestaViewSet)
router.register(r'Opcion', views.OpcionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]

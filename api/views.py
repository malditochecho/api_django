from rest_framework import permissions
from rest_framework import viewsets
from api import models
from api import serializers


class EncuestaViewSet(viewsets.ModelViewSet):
    """
    Este viewset automaticamente provee:
    `list`, `create`, `retrieve`, `update` and `destroy`
    """
    queryset = models.Encuesta.objects.all()
    serializer_class = serializers.EncuestaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class OpcionViewSet(viewsets.ModelViewSet):
    """
    Este viewset automaticamente provee:
    `list`, `create`, `retrieve`, `update` and `destroy`
    """
    queryset = models.Opcion.objects.all()
    serializer_class = serializers.OpcionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

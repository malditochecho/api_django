from rest_framework import serializers

from api import models


class OpcionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Opcion
        fields = ['nombre']


class EncuestaSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='encuesta-detail')

    class Meta:
        model = models.Encuesta
        fields = ['url', 'id', 'nombre', 'comentario', 'opciones']

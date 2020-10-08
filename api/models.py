from django.db import models


class Opcion(models.Model):
    nombre = models.CharField(max_length=255, null=True, blank=False)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Encuesta(models.Model):
    nombre = models.CharField(max_length=255, null=True, blank=False)
    comentario = models.TextField(null=True, blank=True)
    opciones = models.ManyToManyField(Opcion, blank=True)
    
    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return self.nombre

# Crear directorio del proyecto
```bash
mkdir encuesta
cd encuesta
```

# Crear documentacion (esta misma)
```bash
touch readme.MD
```

# Entorno virtual
```bash
python3 -m venv env
source env/bin/activate
pip list
pip install --upgrade pip
pip install Django djangorestframework django-cors-headers psycopg2-binary
pip list
```

# Crear proyecto django y app django
```bash
django-admin startproject encuestas
ls -l
cd encuestas
python manage.py startapp api
ls -l
```

# GIT
```bash
git init
git config --global user.email 'sergrodrig@gmail.com'
git config --global user.name 'Sergio Rodriguez'
git add -A
git commit -m 'setup django'
```

# VSCode
```bash
code .
```


# Django

- Modificar el `settings.py` del proyecto

```python
# Archivo
# encuestas/settings.py

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'api.apps.ApiConfig',
    'rest_framework',
    'corsheaders',
    ...
]

MIDDLEWARE = [
    ...
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'encuestas',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'

CORS_ALLOW_ALL_ORIGINS = True

```
- Realizar migraciones iniciales

```bash
python manage.py migrate
```

- Crear superuser

```bash
python manage.py createsuperuser
```

- Levantar servidor de desarrollo de python

```bash
python manage.py runserver
```

Se puede revisar en http://localhost:8080 y la interfaz de administracion en http://localhost:8080/admin

- Commit

```bash
git add -A
git commit -m 'server Django arriba con la interfaz de admin funcionando y las tablas base migradas en postgres'
```

- Crear modelos en el archivo `api/models.py`

```python
# Archivo
# api/models.py

from django.db import models

# Create your models here.
class Opcion(models.Model):
    nombre = models.CharField(max_length=255, null=True, blank=True)


class Encuesta(models.Model):
    nombre = models.CharField(max_length=255, null=True, blank=True)
    comentario = models.TextField(null=True, blank=True)
    opciones = models.ManyToManyField(Opcion)
```

- Crear migraciones y luego migrar

```bash
python manage.py makemigrations
python manage.py migrate
```

- Agregar tablas al admin de Django en el archivo `api/admin.py`

```python
# Archivo
# api/admin.py

from django.contrib import admin

from api import models

# Register your models here.
admin.site.register(models.Opcion)
admin.site.register(models.Encuesta)
```

- Commit

```bash
git add -A
git commit -m 'modelos creados y migrados. tambien fueron agregados al admin'
```

- Modificar la representacion de los modelos para el admin en el archivo `api/models.py`

```python
# Archivo
# api/models.py

class Opcion(models.Model):
    ...
    def __str__(self):
        return self.nombre


class Encuesta(models.Model):
    ...
    def __str__(self):
        return self.nombre
```

- Commit

```bash
git add -A
git commit -m 'django funcional'
```

# DRF

## Crear serializador

```bash
touch api/serializers.py
```

```python
# Archivo
# api/serializers.py

from rest_framework import serializers

from api import models


class EncuestaSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=True, max_length=255)
    comentario = serializers.CharField()
    opciones = serializers.CharField()
    
    def create(self, validated_data):
        """
        Create and return a new `Encuesta` instance, given the validated data.
        """
        return Encuesta.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Encuesta` instance, given the validated data.
        """
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.comentario = validated_data.get('comentario', instance.comentario)
        instance.opcion = validated_data.get('opcion', instance.opcion)
        instance.save()
        return instance
```
Para probar el serializador podemos usar python shell de Django:

```bash
./manage.py shell
```
Primero serializamos un modelo de DB a Json pasando por data types nativo de Python:
```bash
from api.models import Encuesta, Opcion
from api.serializers import EncuestaSerializer, OpcionSerializer

encuesta = Encuesta(nombre='que cosa?')
encuesta.save()

type(encuesta)
<class 'api.models.Encuesta'>

serializer = EncuestaSerializer(encuesta)

serializer.data
{'nombre': 'que cosa?', 'comentario': None, 'opciones': 'api.Opcion.None'}

content = JSONRenderer().render(serializer.data)
print(content)
b'{"nombre":"que cosa?","comentario":null,"opciones":"api.Opcion.None"}'
```
Tambien podemos deserializar un Json a un modelo de DB:

```bash
./manage.py shell

import io
stream = io.BytesIO(content)
data = JSONParser().parse(stream)

serializer = SnippetSerializer(data=data)
serializer.is_valid()
serializer.validated_data
serializer.save()
```
## Refactorizar serializers

El serializer replica mucho codigo que ya esta en models.py por lo tanto se podria refactorizar usando otras caracteristicas de DRF. Al igual que Django tiene `Form` y `ModelForm`, DRF tiene las clases `Serializer` y `ModelSerializer`.

En el archivo `serializers.py` reemplacemos la clase `EncuestaSerializer` con lo siguiente:

```python
# Archivo
# api/serializers.py

class EncuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Encuesta
        fields = ['nombre', 'comentario', 'opciones']
```

Con python shell podemos inspeccionar todos los campos del la instancia del serializer que ahora estan abstraidas en la clase ModelSerializer, tal como la definimos anteriormente:

```bash
from api.serializers import EncuestaSerializer
serializer = EncuestaSerializer()
print(repr(serializer))
...
```

`ModelSerializer` simplemente crea la clase de serializer por uno. Automaticamente determina los campos, e implementa los metodos `create()` y `update()`.

Escribamos una `view` de Django utilizando el serializer recien creado. Esta sera una view pura de Django, sin utilizar otras caracteristicas de DRF aun.

En el archivo `api/views.py` agregar lo siguiente:

```python
# Archivo
# api/views.py

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from api import models, serializers

@csrf_exempt
def lista_encuestas(request):
    """
    Lista todas las encuestas o crea una nueva.
    """
    if request.method == 'GET':
        encuestas = models.Encuesta.objects.all()
        serializer = serializers.EncuestaSerializer(encuestas, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = EncuestaSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def detalle_encuesta(request, pk):
    """
    Trae, actualiza o elimina una encuesta.
    """
    try:
        encuesta = Encuesta.objects.get(pk=pk)
    except Encuesta.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = EncuestaSerializer(encuesta)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = EncuestaSerializer(encuesta, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        encuesta.delete()
        return HttpResponse(status=204)
```

Agregamos las rutas para hacer las pruebas en el archivo `api/urls.py` y modificamos las rutas padre del proyecto

```bash
touch api/urls.py 
```

```python
# Archivo
# api/urls.py

from django.urls import path
from api import views

urlpatterns = [
    path('encuesta/', views.lista_encuestas),
    path('encuesta/<int:pk>/', views.detalle_encuesta),
]
```

```python
# Archivo
# encuestas/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
```
Para probar ejecutamos el servidor y visitamos el endpoint de la API:

```bash
./manage.py runserver
```

http://127.0.0.1:8000/api/encuesta/

Podemos agregar el ID por ejemplo al serializer para que lo entregue en la respuesta de la API:

```python
# Archivo
# api/serializers.py

...
class EncuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Encuesta
        fields = ['id', 'nombre', 'comentario', 'opciones']
```

## Refactorizar views con rest_framework.Response

Hasta ahora funciona bien la API pero no se estan controlando casos de borde como que el JSON traiga algun dato invalido por ejemplo, pero eso alargaria el codigo bastante por lo que vamos a comenzar a utilizar otras caracteristicas de DRF para que el codigo sea mas conciso.

Realizamos un commit para guardar los cambios hasta este punto:

```bash
git add -A
git commit -m 'serializer implementado con Django puro y luego refactorizado con ModelSerializer de DRF. Vista implementada con Django puro'
```

Reemplazamos el codigo de las views con lo siguiente:

```python
# Archivo
# api/views.py

from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api import models, serializers


@api_view(['GET', 'POST'])
def lista_encuestas(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        encuestas = models.Encuesta.objects.all()
        serializer = serializers.EncuestaSerializer(encuestas, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = serializers.EncuestaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def detalle_encuesta(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        encuesta = models.Encuesta.objects.get(pk=pk)
    except Encuesta.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serializers.EncuestaSerializer(encuesta)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = serializers.EncuestaSerializer(encuesta, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

El codigo se ve muy parecido pero esta un poco mas conciso pero aun le falta para aprovechar al maximo DRF.
Una de las diferencias con el codigo anterior es que las respuestas ya no estan atadas a un content type especifico (JSON) sino que son manejadas dinamicamente. Por ejemplo el cliente podria solicitar la data en JSON asi como tambien podria solicitarla en otro formato como texto plano.

Por ejemplo asi:
||||
|-|-|-|
|http://127.0.0.1:8000/encuesta/|Accept:application/json|# Request JSON|
|http://127.0.0.1:8000/encuesta/|Accept:text/html|# Request HTML|
||||

Ademas como DRF maneja la respuesta, por defecto en los browsers, entrega la interfaz navegable de DRF en vez del JSON en plano.

## Refactorizar views con ModelViews

Ahora podemos refactorizas las vistas del archivo `views.py` con vistas basadas en clases a diferencia de las actuales que son basadas en funciones.

Estas clases implementan un patron que permiten reutilizar codigo para funcionalidades comunes que uno suele encontrarse en la mayoria de las API. Esto sigue la filosofia DRY.

```python
# Archivo
# api/views.py

from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api import models, serializers


class EncuestaList(APIView):
    """
    Lista todas las encuestas o crea una nueva.
    """
    def get(self, request, format=None):
        encuesta = model.Encuestas.objects.all()
        serializer = EncuestasSerializer(encuesta, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = EncuestasSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncuestaDetail(APIView):
    """
    Trae, actualiza o elimina una encuesta.
    """
    def get_object(self, pk):
        try:
            return model.Encuestaobjects.get(pk=pk)
        except EncuestaDoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        encuesta = self.get_object(pk)
        serializer = serializers.EncuestaSerializer(encuesta)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        encuesta = self.get_object(pk)
        serializer = serializers.EncuestaSerializer(encuesta, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        encuesta = self.get_object(pk)
        encuesta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

Tambien hay que modificar el archivo `urls.py`:

```python
# Archivo
# api/urls.py

from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from snippets import views

urlpatterns = [
    path('snippets/', views.SnippetList.as_view()),
    path('snippets/<int:pk>/', views.SnippetDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
```

Al ejecutar el servidor nuevamente la API tiene el mismo funcionamiento, pero a nivel de codigo esta un poco mas organizado. Hay metodos en la clase por cada metodo HTTP a diferencia de antes que estaban todos agrupados en el decorador y se tenian que identificar comparando con if's.

## Refactorizar views con Mixins

La gracias de las vistas basadas en clase de DRF es que permite reutilizar comportamientos comunes de las API. Por ejemplo las operaciones de CRUD que implementamos muy probablemente seran utilizadas en todos los modelos futuros. Dichos comportamientos estan ya implementados en las clases Mixin de DRF.

```python
# Archivo
# api/views.py

from rest_framework import mixins
from rest_framework import generics
from api import models, serializers

class EncuestaList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    queryset = models.Encuesta.objects.all()
    serializer_class = serializers.EncuestaSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class EncuestaDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    queryset = models.Encuesta.objects.all()
    serializer_class = serializers.EncuestaSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
```

En este refactoring si se ve mucho mas conciso el codigo. En la clase se hereda primero `generics.GenericAPIView` que es la base de la vista, y ademas se heredan las clases `mixins.ListModelMixin` y `mixins.CreateModelMixin` en la clase `EncuestaList` que necesita listar las encuestas y crear nuevas, lo que corresponde a la accion `.list()` y `.create()`. Esas acciones vienen en las clases heredadas.

Para el caso de la clase `EncuestaDetail` que necesita un CRUD completo de una instancia de un modelo, se heredan las clases `mixins.RetrieveModelMixin`, `mixins.UpdateModelMixin` y `mixins.DestroyModelMixin`.

De manera muy resumida esto es lo que hace cada clase para entender por que se aplican a estas vistas en este caso:

|||
|-|-|
|ListModelMixin|Lista un queryset y devuelve un codigo 200 con una representacion serializada del queryset en el body del response|
|CreateModelMixin|Crea y guarda una instancia de un modelo. Devuelve un codigo 201 si es exitoso y un 400 si la solicitud es invalida. En ambas devuelve en el body ya sea la representacion serializada de la instancia del modelo, o el error.|
|RetrieveModelMixin|Provee un metodo para devolver solo una instancia de un modelo y devuelve un codigo 200 con una representacion serializada del queryset en el body del response. Si no se encuentra devuelve un 404.|
|UpdateModelMixin|Provee un metodo para actualizar y guardar una instancia de un modelo. Devuelve un codigo 200 si es exitoso y 400 si el request es invalido.|
|DestroyModelMixin|Elimina una instancia de un modelo existente. Devuelve un 204 si es exitoso y un 404 si no se encuentra la instancia.|
|||

Aca hay un resumen de todas las opciones de DRF en cuanto a views, clases, viewsets y serializers.
http://www.cdrf.co/


## Refactorizar con generic class-based views

DRF trae unas clases que ya vienen mezclados algunos mixin para casos tipicos como el nuestro. Por ejemplo listar y agregar instancias de un modelo como en la clase `EncuestaList`.

Modifiquemos el archivo `views.py` nuevamente:

```python
# Archivo
# api/views.py

from rest_framework import generics
from api import models, serializers


class EncuestaList(generics.ListCreateAPIView):
    queryset = models.Encuesta.objects.all()
    serializer_class = serializers.EncuestaSerializer


class EncuestaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Encuesta.objects.all()
    serializer_class = serializers.EncuestaSerializer
```

Esta vez el codigo esta considerablemente mas limpio.
En este caso por ejemplo se utilizó la clase `ListCreateAPIView` que encapsula las clases `GenericAPIView`, `ListModelMixin` y `CreateModelMixin` utilizadas anteriormente y solo requiere especificar el queryset y el serializador a utilizar.

## Refactorizar con ViewSets

Modifiquemos el archivo `views.py`:

```python
# Archivo
# api/views.py

from rest_framework import viewsets
from api import models, serializers


class EncuestaViewSet(viewsets.ModelViewSet):
    """
    Este viewset automaticamente provee:
    `list`, `create`, `retrieve`, `update` and `destroy`
    """
    queryset = models.Encuesta.objects.all()
    serializer_class = serializers.EncuestaSerializer
```

Hasta ahora es el mas conciso de todos. Se pueden combinar todas las operaciones en una sola clase solo especificando el queryset y el serializer.

Para hacer uso del viewset, se debe utilizar un router de DRF.

```python
# Archivo
# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'encuestas', views.EncuestaViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
```

Al ejecutar el servidor vemos que sigue teniendo el mismo funcionamiento, asi como tambien una raiz donde podemos encontrar los modelos que tengamos registrados en el router.

http://127.0.0.1:8000/api/

## Autenticación

Vamos a agregar autenticacion a la API para que los usuarios tengan que estar logeados al crear un registro:

```python
# Archivo
# api/views.py

from rest_framework import permissions
...

class EncuestaViewSet(viewsets.ModelViewSet):
    ...
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
```

Ahora si tratamos de crear un registro con el metodo POST la API nos dice que no estamos autenticados. De hecho en la API navegable de DRF si no estamos autenticados no nos muestra el formulario de POST en la parte inferior de la pagina.

Una forma temporal de autenticarse es mediante el admin de Django. Pero la idea es que se haga todo a traves del enpoint `api` en este caso.

Agregamos lo siguiente al archivo `urls`:

```python
# Archivo
# api/urls.py

from django.urls import path, include

urlpatterns = [
    ...
    path('auth/', include('rest_framework.urls')),
]
```

Ahora en la parte superior de la pagina nos entrega un menu para poder logearnos con los usuarios de Django, los mismos del Django admin.

Actualmente se utilizan las clases de autenticacion por defecto `SessionAuthentication` y `BasicAuthentication` ya que no hemos especificado ninguna. Esto significa que uno se puede autenticar en el browser y tambien reconoce la sesion mientras este autenticado. En el caso de consumir la API programaticamente hay que enviar las credenciales con cada solicitud.

## HyperLinked API

Actualmente en la API al hacer un list nos muestra todas las instancias del modelo, pero el campo que tiene el ForeignKey hacia el otro modelo sale representado como un arreglo de los id del otro modelo. Esto no es muy explicito. Ademas para ver el detalle de una instancia debo especificarlo en el endpoint lo que le quita sentido a la API navegable de DRF.

Para solucionar esto usaremos otra clase de serializer que trae DRF llamada `HyperLinkedModelSerializer`.

Modifiquemos el archivo `serializers.py`:

```python
# Archivo
# api/serializers.py
class OpcionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Opcion
        fields = ['nombre']

class EncuestaSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='encuesta-detail')

    class Meta:
        model = models.Encuesta
        fields = ['url', 'id', 'nombre', 'comentario', 'opciones']
````
Le aplicamos `HyperLinkedModelSerializer` a la clase EncuestaSerializer para que en la API muestre un campo mas que corresponda a una URL unica correspondiente a dicha instancia del modelo.

En el serializer hay que agregar un campo llamado url que correspondera a la URL.

## Paginacion

Por ultimo vamos a paginar los resultados.

Para hacerlo simple estableceremos un parametro de paginacion que afecta a todos los modelos. Se puede crear una paginacion personalizada por cada modelo por separado pero para este caso no es necesario.

En el settings agregamos esta configuracion:

```python
# Archivo
# encuestas/settings.py
...
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
...
```

Esto permite que la API venga paginada en paginas de 10 elementos en este caso.
Ademas cada resultado entrega una URL que permite ver los 10 siguientes y los 10 anteriores.
from django.urls import path
from . import views


app_name = "categorias"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("crear/", views.crear, name="crear"),
    path("editar/<str:id>/", views.editar, name="editar"),
    path("eliminar/<str:id>/", views.eliminar, name="eliminar"),
]
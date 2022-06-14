from django.urls import path
from . import views



urlpatterns = [
    path('', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('home', views.home, name='home'),
    path('usuarios', views.usuarios, name='usuarios'),
    path('usuarios/nuevo_usuario', views.nuevoUsuario, name='nuevoUsuario'),
    path('usuarios/<int:id_user>', views.cambiarEstadoUsuario, name='cambiarEstadoUsuario'),
    path('usuarios/editar_usuario/<int:id_user>', views.editarUsuario, name='editarUsuario'),
    path('editar_perfil/<int:id_user>', views.editarPerfil, name='editarPerfil'),
    path('config/admin', views.config, name='config'),
    path('404', views.error404, name='error404'),
    
    
]
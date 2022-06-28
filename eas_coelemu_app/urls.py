from django.urls import path
from . import views



urlpatterns = [
    path('', views.login, name = 'login'),
    path('config/admin', views.config, name = 'config'),
    path('logout', views.logout, name = 'logout'),
    path('home', views.home, name = 'home'),
    path('usuarios', views.usuarios, name = 'usuarios'),
    path('usuarios/nuevo_usuario', views.nuevoUsuario, name = 'nuevoUsuario'),
    path('usuarios/<int:id_user>', views.cambiarEstadoUsuario, name ='cambiarEstadoUsuario'),
    path('usuarios/editar_usuario/<int:id_user>', views.editarUsuario, name = 'editarUsuario'),
    path('editar-perfil/<int:id_user>', views.editarPerfil, name = 'editarPerfil'),
    path('precio-gas', views.precioGas, name = 'precioGas'),
    path('precio-gas/nuevo_precio', views.nuevoPrecio, name = 'nuevoPrecio'),
    path('descuento-aplicable', views.descuentoAplicable, name = 'descuentoAplicable'),
    path('nuevo-descuento', views.nuevoDescuento, name = 'nuevoDescuento'),
    path('editar-descuento/<int:id_descuento>', views.editarDescuento, name = 'editarDescuento'),
    path('eliminar-descuento/<int:id_descuento>', views.eliminarDescuento, name = 'eliminarDescuento'),
    path('cantidad-convenios', views.cantConvenios, name = "cantConvenios"),
    path('nuevo-cantidad-convenios', views.nuevoCantConvenios, name = "nuevoCantConvenios"),
    path('nuevo-hogar/<int:id_user>', views.nuevoHogar, name = 'nuevoHogar'),
    path('404', views.error404, name='error404'),
    
    
]
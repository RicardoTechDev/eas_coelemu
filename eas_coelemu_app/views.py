from multiprocessing import context
from re import template
from django.conf import Settings
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib import messages
from eas_coelemu_app.models import Usuario, Rol
from eas_coelemu_app.decorators import loginRequired
from eas_coelemu_app.functions import *
#para en envío de correos
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

import bcrypt
import random as rd
import string
from typing import List

def config(request):
    usuario = ''

    existe_rol = Rol.objects.all()
    if not existe_rol:
        #Creamos los Roles
        administrador = Rol.objects.create(
            nombre = 'Administrador',
            descripcion = 'Usuario con acceso total a la aplicación'
        )
        director = Rol.objects.create(
            nombre = 'Director',
            descripcion = 'Usuario con acceso restringido'
        )
        asistente = Rol.objects.create(
            nombre = 'Asistente',
            descripcion = 'Usuario con acceso restringido'
        )
        beneficiario = Rol.objects.create(
            nombre = 'Beneficiario',
            descripcion = 'Usuario con acceso mínimo'
        )
    else:
        rol_admin = Rol.objects.get(nombre='Administrador')
        usuario = Usuario.objects.filter(rol = rol_admin)

    
    
    if usuario:#si ya existe un usuario administrador redirigimos a una página de error
        return render(request, '404.html',)


    if request.method == 'POST':
        #traemos el diccionario con errores para verificar si existen
        errors = Usuario.objects.validador_basico(request.POST)
        if len(errors) > 0:
            #si el diccionario de errores contiene algo, recorra cada par clave-valor y cree un mensaje flash
            for key, value in errors.items():
                messages.error(request, value)
                request.session['registro_nombres'] =  request.POST['registro_nombres']
            # redirigir al usuario al formulario para corregir los errores
            return redirect(f'config')

        else:
            # si el objeto de errores está vacío, eso significa que no hubo errores.
            #delsession(request)#vaciamos las variables de sesión del registro
            registro_admin_rut = formRut(request.POST['registro_rut'])
            #encriptación de la contraseña ingresada por el usuario
            password_encryp = bcrypt.hashpw(request.POST['registro_contrasena'].encode(), bcrypt.gensalt()).decode()

            new_user = Usuario.objects.create(
                                            nombres = request.POST['registro_nombres'],
                                            apellido_paterno = request.POST['registro_ap_paterno'],
                                            apellido_materno = request.POST['registro_ap_materno'],
                                            rut = int(registro_admin_rut['rut']),
                                            dv = registro_admin_rut['dv'],
                                            imagen = '',
                                            celular = request.POST['registro_celular'],
                                            email = request.POST['registro_email'],
                                            contrasena = password_encryp,
                                            rol = rol_admin,#instancia de Rol
                                            estado= 1
                                            )
            
            request.session['usuario'] = {
                                            "id" : new_user.id,
                                            "name" : f"{new_user}",
                                            "email" : new_user.email,
                                            "rol" : new_user.rol.nombre
                                        }
            
            messages.success(request, f'Se realizado el registro del administrador con exito.')
            return redirect("/home") 

    else: #metodo GET
        
        return render(request, 'admin/register.html',)


def login(request):
    errors = {}

    if request.method == 'POST':
        if request.POST['rut_login'] == '':
            messages.error(request,"Debe ingresar un RUT.")
            return redirect("/")#redirigimos al login

        if request.POST['contrasena_login'] == '':
            messages.error(request, "Debe ingresar la contraseña.")
            return redirect("/")#redirigimos al login
        
        else:
            #buscamos el rut de usuario ingresado en la base de datos (si existe) y asignamos a la variable user
            usuario = Usuario.objects.filter(rut=request.POST['rut_login'])

            if usuario: #una lista vacía devolverá falso
                #si existe tomamos el primer elemento de la lista user (devuelto por filter)
                log_user = usuario[0]

                #validamos la contraseña ingresada por el usuario 
                if bcrypt.checkpw(request.POST['contrasena_login'].encode(), log_user.contrasena.encode()):
                    # si obtenemos True después de validar la contraseña, podemos poner la identificación del usuario en la sesión
                    usuario_logueado = {
                        "id" : log_user.id,
                        "nombre" : f"{log_user}", # usamos el "def __str__(self)" definido en el modelo con return f"{self.firstname} {self.lastname}"
                        "email" : log_user.email,
                        "rol" : log_user.rol.nombre
                    }

                    request.session['usuario'] = usuario_logueado
                    #delsession(request)#vaciamos las variables de sesión del registro

                    return redirect("home")

                else:#si la contraseña no coincide enviamos un mensaje de error al usuario
                    messages.error(request, "Rut o Contraseña invalidos.")
                    return redirect("login")#redirigimos al login
            
            else:#si la lista esta vacia significa que no se encontro el email ingresado
                #enviamos un mensaje de error al usuario
                messages.error(request, "Rut o Contraseña invalidos.")
                return redirect("login")#redirigimos al login
        

    else: 
        if 'usuario'  in request.session:
            messages.error(request, "Usted ya está logeado.")
            return redirect("home")

        return render(request, 'index.html')


def logout(request):
    if 'usuario' in request.session:
        del request.session['usuario']  
        #request.session.flush()
        #request.session.delete()
    
    return redirect("login")


@loginRequired #consultamos si el usuario no está logueado 
def home(request):
    if request.session['usuario']['rol'] == 'Administrador':
        context = {
            'usuarios' : Usuario.objects.all(),
            'cant_usuarios' : Usuario.objects.all().count()
        }
        return render(request, 'admin/home.html', context)


@loginRequired
def usuarios(request):
    usuarios = Usuario.objects.all()
    
    context = {
            'usuarios' : usuarios,     
    }

    return render(request, 'admin/usuarios/usuarios_registrados.html', context)



@loginRequired
def nuevoUsuario(request):
    if request.method == 'GET':
        context = {
                'roles':  Rol.objects.all() #.exclude(rol__nombre='Adminstrador')
                }
        return render(request, 'admin/usuarios/nuevo_usuario.html', context)

    elif request.method == 'POST':
        errors = Usuario.objects.validador_basico(request.POST)
        rut_nuevo_registro = formRut(request.POST['registro_rut'])


        if Usuario.objects.filter(rut=int(rut_nuevo_registro['rut'])).exists():
            errors['existe_registro'] = f"El usuario con RUT {request.POST['registro_rut']} ya se encuentra registrado."; 

        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevoUsuario)
        
        else:
            new_password = crearPass()
            password_encryp = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            rol_usuario = Rol.objects.get(nombre = 'Asistente')
            imagen_usuario = ''
            
            if request.FILES.get('registro_imagen'):
                imagen_usuario = request.FILES['registro_imagen']

            new_user = Usuario.objects.create(
                                            nombres = request.POST['registro_nombres'],
                                            apellido_paterno = request.POST['registro_ap_paterno'],
                                            apellido_materno = request.POST['registro_ap_materno'],
                                            rut = int(rut_nuevo_registro['rut']),
                                            dv = rut_nuevo_registro['dv'],
                                            imagen = imagen_usuario,
                                            celular = request.POST['registro_celular'],
                                            email = request.POST['registro_email'],
                                            contrasena = password_encryp,
                                            rol = Rol.objects.get(id=request.POST['registro_rol']),
                                            estado= 1
                                            )
            
            request.session['usuario'] = {
                                            "id" : new_user.id,
                                            "name" : f"{new_user}",
                                            "email" : new_user.email,
                                            "rol" : new_user.rol.nombre
                                        }
            
            messages.success(request, f"Nuevo usuario registrado con exito.")
            sendWelcomeMail(new_user, new_password)

            
        return redirect(usuarios)
        


def cambiarEstadoUsuario(request, id_user):
    usuario = Usuario.objects.get(id=id_user)
    print(f"Id {id_user} estado {usuario.estado} y id {usuario.id}")

    if usuario.estado == 1:
        usuario.estado = 0
        usuario.save()
    else:
        usuario.estado = 1
        usuario.save()

    return redirect(usuarios)



def editarUsuario(request, id_user):
    usuario = Usuario.objects.get(id=id_user)
    roles = Rol.objects.all()
    if request.method == 'GET':
        context = {
                'usuario':  usuario,
                'roles': roles,
                }
        return render(request, 'admin/usuarios/editar_usuario.html', context)

    elif request.method == 'POST':
        usuario.nombres = request.POST['editar_nombres']
        usuario.apellido_paterno = request.POST['editar_ap_paterno']
        usuario.apellido_materno = request.POST['editar_ap_materno']
        #usuario.imagen = imagen_usuario,
        usuario.celular = request.POST['editar_celular']
        usuario.email = request.POST['editar_email']
        rol = Rol.objects.get(id=request.POST['editar_rol'])#instancia de rol
        usuario.rol = rol 
        usuario.save()

    
    return redirect(usuarios)


def editarPerfil(request, id_user):
    usuario = Usuario.objects.get(id=id_user)
    if request.method == 'GET':
        context = {
                'usuario':  usuario,
                }
        return render(request, 'editar_perfil.html', context)

    elif request.method == 'POST':
        usuario.nombres = request.POST['editar_nombres']
        usuario.apellido_paterno = request.POST['editar_ap_paterno']
        usuario.apellido_materno = request.POST['editar_ap_materno']
        #usuario.imagen = imagen_usuario,
        usuario.celular = request.POST['editar_celular']
        usuario.email = request.POST['editar_email'] 
        usuario.save()

    return redirect("home")


def error404(request):
    return render(request, '404.html')


def crearPass():
    simbolos = ['!','@','#','$','%','&','>','<','*']
    todos = list(string.ascii_letters)+list(string.digits)+simbolos
    contrasena = ''.join(rd.sample(todos, 6))

    return contrasena


def sendWelcomeMail(user, password):
    
    context = {
        'nombre'  : f"{user}",
        'rut'     : user.rut,
        'password': password,
        'mail'    : user.email
    }

    template = get_template('correos/bienvenida.html')
    content = template.render(context)

    email = EmailMultiAlternatives(
        'Un correo de prueba',
        'DIDECO COELEMU',
        settings.EMAIL_HOST_USER,
        [user.email],#destinatarios
        #CC=[], se puede definir con copia a 
    )

    email.attach_alternative(content, 'text/html')#agregar el contenido al correo
    email.send()





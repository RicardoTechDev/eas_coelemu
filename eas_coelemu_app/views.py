#$ python -m pip freeze
from ast import Return
from contextvars import Context
from decimal import Rounded
from http.client import HTTPResponse
from multiprocessing import context
from re import template
from django.conf import Settings
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib import messages
from eas_coelemu_app.models import *
from eas_coelemu_app.decorators import loginRequired
from eas_coelemu_app.functions import *
#para en envío de correos
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
#from datetime import datetime
#Para generar el pdf de convenio
import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders


import bcrypt
import random as rd
import string
from typing import List
import datetime
import re



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
        errors = Usuario.objects.validador_config(request.POST)
        if len(errors) > 0:
            #si el diccionario de errores contiene algo, recorra cada par clave-valor y cree un mensaje flash
            for key, value in errors.items():
                messages.error(request, value)
            # redirigir al usuario al formulario para corregir los errores
            return redirect(f'config')

        else:
            # si el objeto de errores está vacío, eso significa que no hubo errores.
            #delsession(request)#vaciamos las variables de sesión del registro
            registro_admin_rut = formRut(request.POST['registro_rut'])
            #encriptación de la contraseña ingresada por el usuario
            new_password = crearPass()
            password_encryp = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            
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
            
            usuario_logueado = {
                                "id" : new_user.id,
                                "nombre" : f"{new_user}", # usamos el "def __str__(self)" definido en el modelo con return f"{self.firstname} {self.lastname}"
                                "email" : new_user.email,
                                "rol" : new_user.rol.nombre
                            }

            request.session['usuario'] = usuario_logueado
            
            messages.success(request, f'Se a realizado el registro del administrador con exito. Hemos enviado una contraseña temporal al correo { new_user.email }')
            sendWelcomeMail(new_user, new_password)
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
            usuario = Usuario.objects.get(rut=request.POST['rut_login'])
            if usuario: #si esta vacio devolverá falso
                #validamos que el usuario se encuentra activo
                if usuario.estado == 0:
                    messages.error(request, "Usuario inactivo, contacte al administrador de la aplicación.")
                    return redirect("/")#redirigimos al login
                #validamos la contraseña ingresada por el usuario 
                if bcrypt.checkpw(request.POST['contrasena_login'].encode(), usuario.contrasena.encode()):
                    # si obtenemos True después de validar la contraseña, podemos poner la identificación del usuario en la sesión
                    usuario_logueado = {
                        "id" : usuario.id,
                        "nombre" : f"{usuario}", 
                        "email" : usuario.email,
                        "rol" : usuario.rol.nombre
                    }
                    request.session['usuario'] = usuario_logueado
                    return redirect("home")

                else:#si la contraseña no coincide enviamos un mensaje de error al usuario
                    messages.error(request, "Rut o Contraseña invalidos.")
                    return redirect("login")#redirigimos al login
            
            else:
                messages.error(request, "Rut o Contraseña invalidos.")
                return redirect("login")#redirigimos al login
        
    else: 
        if 'usuario'  in request.session:
            messages.error(request, "Usted ya está logeado.")
            return redirect("home")

        return render(request, 'index.html')




@loginRequired
def logout(request):
    if 'usuario' in request.session:
        request.session['usuario'] = ''
        del request.session['usuario']  
        #request.session.flush()
        #request.session.delete()
    
    return redirect("login")


@loginRequired 
def home(request):
    if request.session['usuario']['rol'] == 'Administrador':
        context = {
                    'usuarios' : Usuario.objects.all(),
                    'cant_usuarios' : Usuario.objects.all().count(),
                    'precio_gas' : PrecioGas.objects.get(estado=1),
                    'convenios' : Convenio.objects.all().count(),
                    'solicitudes': Solicitud.objects.all().count(),
                    }
        return render(request, 'admin/home.html', context)

    elif request.session['usuario']['rol'] == 'Director':
        context = {
                    'beneficiarios' : Beneficiario.objects.all(),
                    'cant_beneficiarios' : Beneficiario.objects.all().count(),
                    'precio_gas' : PrecioGas.objects.get(estado=1),
                    'convenios' : Convenio.objects.all().count(),
                    'solicitudes': Solicitud.objects.all().count(),
                    }
        return render(request, 'director/home.html', context)

    elif request.session['usuario']['rol'] == 'Asistente':
        context = {
                    'beneficiarios' : Beneficiario.objects.all(),
                    'cant_beneficiarios' : Beneficiario.objects.all().count(),
                    'precio_gas' : PrecioGas.objects.get(estado=1),
                    'convenios' : Convenio.objects.all().count(),
                    'solicitudes': Solicitud.objects.all().count(),
                }
        return render(request, 'asistente/home.html', context)

    elif request.session['usuario']['rol'] == 'Beneficiario':
        context = {
            'precio_gas' : PrecioGas.objects.complex_filter(estado=1),
        }
        return render(request, 'beneficiario/home.html', context)


@loginRequired
def usuarios(request):
    usuarios = Usuario.objects.all()
    rol_beneficiario = Rol.objects.get(nombre='Beneficiario')
    beneficiarios = Usuario.objects.filter(rol=rol_beneficiario.id)
    context = {
            'usuarios' : usuarios,
            'beneficiarios' : beneficiarios     
    }
    if request.session['usuario']['rol'] == 'Administrador':
        return render(request, 'admin/usuarios/usuarios_registrados.html', context)
    elif request.session['usuario']['rol'] == 'Asistente' or request.session['usuario']['rol'] == 'Director':
        return render(request, 'asistente/usuarios/beneficiarios_registrados.html', context)
    else:
        return redirect('error404')



@loginRequired
def beneficiariosGruposFamiliares(request):
    rol_beneficiario = Rol.objects.get(nombre='Beneficiario')
    beneficiarios = Usuario.objects.filter(rol=rol_beneficiario.id)
    context = {
            'beneficiarios' : beneficiarios     
            }
    return render(request, 'admin/grupo_familiar/beneficiarios_grupos_familiares.html', context)




@loginRequired
def nuevoUsuario(request):
    if request.method == 'GET':
        rol_beneficiario = Rol.objects.get(nombre = 'Beneficiario')
        context = {
                'roles':  Rol.objects.all(), #.exclude(rol__nombre='Adminstrador')
                'id_rol_beneficiario' : rol_beneficiario.id
                }
        if request.session['usuario']['rol'] == 'Administrador':
            return render(request, 'admin/usuarios/nuevo_usuario.html', context)
        else:
            return redirect('error404')
        
    elif request.method == 'POST':
        errors = Usuario.objects.validador_basico(request.POST)
        rut_nuevo_registro = formRut(request.POST['registro_rut'])
        #Variables de session para guardar los datos en caso de error el usuario no tenga que escribir todo
        request.session['registro_nombres'] =  request.POST['registro_nombres']
        request.session['registro_ap_paterno'] = request.POST['registro_ap_paterno']
        request.session['registro_ap_materno'] = request.POST['registro_ap_materno']
        request.session['registro_rut'] = request.POST['registro_rut']
        request.session['registro_celular'] = request.POST['registro_celular']
        request.session['registro_email'] = request.POST['registro_email']
        request.session['registro_rol'] = request.POST['registro_rol']
        request.session['rsh_calificacion'] = request.POST['rsh_calificacion']
        request.session['rsh_direccion'] = request.POST['rsh_direccion']
    
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(nuevoUsuario)
        
        #Si el rut ya se encuentra registrado
        if Usuario.objects.filter(rut=int(rut_nuevo_registro['rut'])).exists():
            errors['existe_registro'] = f"El usuario con RUT {request.POST['registro_rut']} ya se encuentra registrado."; 
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(nuevoUsuario)

        #si el rut no está registrado
        else:
            new_password = crearPass()
            password_encryp = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            rol_nuevo_usuario = Rol.objects.get(id=request.POST['registro_rol'])
            rsh_beneficiario = ''
            
            if rol_nuevo_usuario.nombre != 'Beneficiario' and request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
                new_user = Usuario.objects.create(
                                                nombres = request.POST['registro_nombres'],
                                                apellido_paterno = request.POST['registro_ap_paterno'],
                                                apellido_materno = request.POST['registro_ap_materno'],
                                                rut = int(rut_nuevo_registro['rut']),
                                                dv = rut_nuevo_registro['dv'],
                                                imagen = '',
                                                celular = request.POST['registro_celular'],
                                                email = request.POST['registro_email'],
                                                contrasena = password_encryp,
                                                rol = rol_nuevo_usuario,
                                                estado= 1
                                                )
                sendWelcomeMail(new_user, new_password)

                messages.success(request, f"Nuevo usuario registrado con exito.")

            else:
                errors = GrupoFamiliar.objects.validador_basico(request.POST)
                if len(errors) > 0:
                    for key, value in errors.items():
                        messages.error(request, value)
                    return redirect(nuevoUsuario)
                
                else:
                    if request.FILES.get('rsh_pdf'):
                        rsh_beneficiario = request.FILES['rsh_pdf']

                    new_user = Usuario.objects.create(
                                                nombres = request.POST['registro_nombres'],
                                                apellido_paterno = request.POST['registro_ap_paterno'],
                                                apellido_materno = request.POST['registro_ap_materno'],
                                                rut = int(rut_nuevo_registro['rut']),
                                                dv = rut_nuevo_registro['dv'],
                                                imagen = '',
                                                celular = request.POST['registro_celular'],
                                                email = request.POST['registro_email'],
                                                contrasena = password_encryp,
                                                rol = rol_nuevo_usuario,
                                                estado= 1
                                                )
                    sendWelcomeMail(new_user, new_password)

                    new_grupo_familiar = GrupoFamiliar.objects.create(
                                                calif_soc_eco = request.POST['rsh_calificacion'],
                                                direccion = request.POST['rsh_direccion'],
                                                rsh_archivo = rsh_beneficiario,
                                                estado = 1
                                                )
                    new_beneficiario = Beneficiario.objects.create(
                                                grupo_familiar = new_grupo_familiar,
                                                usuario = new_user,
                                                estado = 1
                                                )
                    messages.success(request, f"Nuevo usuario beneficiario registrado con exito.")

        delVaSessionUsuarios(request)
        return redirect(usuarios)
        


def delVaSessionUsuarios(request):
    del request.session['registro_nombres']
    del request.session['registro_ap_paterno']
    del request.session['registro_ap_materno']
    del request.session['registro_rut']
    del request.session['registro_celular']
    del request.session['registro_email']
    del request.session['registro_rol']
    del request.session['rsh_calificacion']
    del request.session['rsh_direccion']
    



def delVaSessionIntegrante(request):
    del request.session['nombres_integrante']
    del request.session['ap_paterno_integrante']
    del request.session['ap_materno_integrante']
    del request.session['rut_integrante']
    del request.session['parentesco']



def cambiarEstadoUsuario(request, id_user):
    usuario = Usuario.objects.get(id=id_user)
    if usuario.estado == 1:
        usuario.estado = 0
        usuario.save()
    else:
        usuario.estado = 1
        usuario.save()

    return redirect(usuarios)



def editarUsuario(request, id_user):
    if 'usuario' not in request.session:
        return redirect('error404')

    usuario = Usuario.objects.get(id=id_user)
    roles = Rol.objects.all()
    grupo_familiar = ''
    rol_beneficiario = Rol.objects.get(nombre = 'Beneficiario')
    
    if request.method == 'GET':
        if usuario.rol.nombre == 'Beneficiario':#para obtener los datos de grupo familiar 
            beneficiario = Beneficiario.objects.get(usuario=usuario.id)
            grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
            #print(grupo_familiar.id)

        context = {
                'usuario':  usuario,
                'usuario_rut' : (f"{usuario.rut}-{usuario.dv}"),
                'roles': roles,
                'grupo_familiar' : grupo_familiar,
                'id_rol_beneficiario' : rol_beneficiario.id
                }

        if request.session['usuario']['rol'] == 'Administrador':
            return render(request, 'admin/usuarios/editar_usuario.html', context)
        elif request.session['usuario']['rol'] == 'Asistente' or request.session['usuario']['rol'] == 'Director':
            return render(request, 'asistente/usuarios/editar_beneficiario.html', context)
        else:
            return redirect('error404')
        

    elif request.method == 'POST':
        errors = Usuario.objects.validador_basico(request.POST)
        rsh_beneficiario = ''
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(editarUsuario,id_user)

        if request.FILES.get('rsh_pdf'):
            rsh_beneficiario = request.FILES['rsh_pdf']

        #si rol no beneficiario
        rol_usuario_editar = Rol.objects.get(id=request.POST['registro_rol'])
        if rol_usuario_editar.nombre != 'Beneficiario':
            usuario.nombres = request.POST['registro_nombres']
            usuario.apellido_paterno = request.POST['registro_ap_paterno']
            usuario.apellido_materno = request.POST['registro_ap_materno']
            usuario.celular = request.POST['registro_celular']
            usuario.email = request.POST['registro_email']
            rol = Rol.objects.get(id=request.POST['registro_rol'])#instancia de rol
            usuario.rol = rol 
            usuario.save()
            messages.success(request, f"Usuario editado con exito.")

        #si el rol es beneficiario y es el mismo que tenia antes de editar
        if rol_usuario_editar.nombre == 'Beneficiario' and rol_usuario_editar.nombre == usuario.rol.nombre:
            errors = GrupoFamiliar.objects.validador_basico(request.POST)
            if len(errors) > 0:
                for key, value in errors.items():
                    messages.error(request, value);
                return redirect(editarUsuario,id_user)

            
            beneficiario = Beneficiario.objects.get(usuario=usuario.id)
            grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)

            if not grupo_familiar.rsh_archivo: 
                if request.FILES.get('rsh_pdf'):
                    rsh_beneficiario = request.FILES['rsh_pdf']
                else:
                    rsh_beneficiario = ''
            else:
                if request.FILES.get('rsh_pdf'):
                    rsh_beneficiario = request.FILES['rsh_pdf']
                else:
                    rsh_beneficiario = grupo_familiar.rsh_archivo

            usuario.nombres = request.POST['registro_nombres']
            usuario.apellido_paterno = request.POST['registro_ap_paterno']
            usuario.apellido_materno = request.POST['registro_ap_materno']
            usuario.celular = request.POST['registro_celular']
            usuario.email = request.POST['registro_email']
            usuario.rol = Rol.objects.get(id=request.POST['registro_rol'])#instancia de rol
            grupo_familiar.calif_soc_eco = request.POST['rsh_calificacion']
            grupo_familiar.direccion = request.POST['rsh_direccion']
            grupo_familiar.rsh_archivo =  rsh_beneficiario
            usuario.save()
            grupo_familiar.save()
            messages.success(request, f"Beneficiario editado con exito.")

        #si el rol es beneficiario y es distinto al que tenia antes de editar
        if rol_usuario_editar.nombre == 'Beneficiario' and rol_usuario_editar.nombre != usuario.rol.nombre:
            errors = GrupoFamiliar.objects.validador_basico(request.POST)
            if len(errors) > 0:
                for key, value in errors.items():
                    messages.error(request, value);
                return redirect(editarUsuario,id_user)

            #comprobar si tenia un beneficiario
            if  Beneficiario.objects.filter(usuario=usuario.id):
                #si lo tenia editamos el grupo familiar asociado al beneficiario asociado al usuario
                beneficiario = Beneficiario.objects.get(usuario=usuario.id)
                grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)

                if not grupo_familiar.rsh_archivo: 
                    if request.FILES.get('rsh_pdf'):
                        rsh_beneficiario = request.FILES['rsh_pdf']
                    else:
                        rsh_beneficiario = ''
                else:
                    if request.FILES.get('rsh_pdf'):
                        rsh_beneficiario = request.FILES['rsh_pdf']
                    else:
                        rsh_beneficiario = grupo_familiar.rsh_archivo

                usuario.nombres = request.POST['registro_nombres']
                usuario.apellido_paterno = request.POST['registro_ap_paterno']
                usuario.apellido_materno = request.POST['registro_ap_materno']
                usuario.celular = request.POST['registro_celular']
                usuario.email = request.POST['registro_email']
                usuario.rol = Rol.objects.get(id=request.POST['registro_rol'])#instancia de rol
                grupo_familiar.calif_soc_eco = request.POST['rsh_calificacion']
                grupo_familiar.direccion = request.POST['rsh_direccion']
                grupo_familiar.rsh_archivo =  rsh_beneficiario
                usuario.save()
                grupo_familiar.save()
                messages.success(request, f"Beneficiario editado con exito.")
            
            else:
                #si no lo tenia creamos un beneficiario y grupo familiar nuevo
                usuario.nombres = request.POST['registro_nombres']
                usuario.apellido_paterno = request.POST['registro_ap_paterno']
                usuario.apellido_materno = request.POST['registro_ap_materno']
                usuario.celular = request.POST['registro_celular']
                usuario.email = request.POST['registro_email']
                usuario.rol = Rol.objects.get(id=request.POST['registro_rol'])#instancia de rol
                usuario.save()
                
                new_grupo_familiar = GrupoFamiliar.objects.create(
                                                calif_soc_eco = request.POST['rsh_calificacion'],
                                                direccion = request.POST['rsh_direccion'],
                                                rsh_archivo = rsh_beneficiario,
                                                estado = 1
                                                )
                new_beneficiario = Beneficiario.objects.create(
                                            grupo_familiar = new_grupo_familiar,
                                            usuario = usuario,
                                            estado = 1
                                            )
    
    return redirect(usuarios)



def verUsuario(request, id_user):
    if 'usuario' not in request.session:
        return redirect('error404')

    usuario = Usuario.objects.get(id=id_user)
    roles = Rol.objects.all()
    grupo_familiar = ''
    rol_beneficiario = Rol.objects.get(nombre = 'Beneficiario')
    
    if request.method == 'GET':
        if usuario.rol.nombre == 'Beneficiario':#para obtener los datos de grupo familiar 
            beneficiario = Beneficiario.objects.get(usuario=usuario.id)
            grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
            #print(grupo_familiar.id)

        context = {
                'usuario':  usuario,
                'usuario_rut' : (f"{usuario.rut}-{usuario.dv}"),
                'roles': roles,
                'grupo_familiar' : grupo_familiar,
                'id_rol_beneficiario' : rol_beneficiario.id
                }
        if request.session['usuario']['rol'] == 'Administrador':
            return render(request, 'admin/usuarios/ver_usuario.html', context)
        elif request.session['usuario']['rol'] == 'Asistente' or request.session['usuario']['rol'] == 'Director':
            return render(request, 'asistente/usuarios/ver_beneficiario.html', context)
        else:
            return redirect('error404')




@loginRequired
def nuevoBeneficiario(request):
    if request.method == 'GET':
        context = {
                }
        if request.session['usuario']['rol'] == 'Asistente' or request.session['usuario']['rol'] == 'Director':
            return render(request, 'asistente/usuarios/nuevo_beneficiario.html', context)
        if request.session['usuario']['rol'] == 'Beneficiario':
            return redirect('error404')

    elif request.method == 'POST':
        errors_beneficiario = Usuario.objects.validador_beneficiario(request.POST)
        errors_grupo_familiar = GrupoFamiliar.objects.validador_basico(request.POST)
        rut_nuevo_registro = formRut(request.POST['registro_rut'])
        rsh_beneficiario = ''
        
        #Variables de session para guardar los datos en caso de error el usuario no tenga que escribir todo
        request.session['registro_nombres'] =  request.POST['registro_nombres']
        request.session['registro_ap_paterno'] = request.POST['registro_ap_paterno']
        request.session['registro_ap_materno'] = request.POST['registro_ap_materno']
        request.session['registro_rut'] = request.POST['registro_rut']
        request.session['registro_celular'] = request.POST['registro_celular']
        request.session['registro_email'] = request.POST['registro_email']
        request.session['rsh_calificacion'] = request.POST['rsh_calificacion']
        request.session['rsh_direccion'] = request.POST['rsh_direccion']

        if len(errors_beneficiario) > 0:
            for key, value in errors_beneficiario.items():
                messages.error(request, value);
            return redirect(nuevoBeneficiario)

        if len(errors_grupo_familiar) > 0:
            for key, value in errors_grupo_familiar.items():
                messages.error(request, value);
            return redirect(nuevoBeneficiario)

        #Si el rut ya se encuentra registrado
        elif Usuario.objects.filter(rut=int(rut_nuevo_registro['rut'])).exists():
            errors_beneficiario['existe_registro'] = f"El usuario con RUT {request.POST['registro_rut']} ya se encuentra registrado."; 
            for key, value in  errors_beneficiario.items():
                messages.error(request, value);
            return redirect(nuevoUsuario)

        else:
            new_password = crearPass()
            password_encryp = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            rol_beneficiario = Rol.objects.get(nombre = 'Beneficiario')
            if request.FILES.get('rsh_pdf'):
                rsh_beneficiario = request.FILES['rsh_pdf']

            new_user = Usuario.objects.create(
                                        nombres = request.POST['registro_nombres'],
                                        apellido_paterno = request.POST['registro_ap_paterno'],
                                        apellido_materno = request.POST['registro_ap_materno'],
                                        rut = int(rut_nuevo_registro['rut']),
                                        dv = rut_nuevo_registro['dv'],
                                        imagen = '',
                                        celular = request.POST['registro_celular'],
                                        email = request.POST['registro_email'],
                                        contrasena = password_encryp,
                                        rol = rol_beneficiario,
                                        estado= 1
                                        )
            sendWelcomeMail(new_user, new_password)

            new_grupo_familiar = GrupoFamiliar.objects.create(
                                        calif_soc_eco = request.POST['rsh_calificacion'],
                                        direccion = request.POST['rsh_direccion'],
                                        rsh_archivo = rsh_beneficiario,
                                        estado = 1
                                        )
            new_beneficiario = Beneficiario.objects.create(
                                        grupo_familiar = new_grupo_familiar,
                                        usuario = new_user,
                                        estado = 1
                                        )
            messages.success(request, f"Nuevo usuario beneficiario registrado con exito.")
    delVaSessionUsuarios(request)
    return redirect(usuarios)



#ok
def miPerfil(request, id_user):
    if 'usuario' not in request.session:
        return redirect('error404')

    if request.session['usuario']['id']!=id_user:
        return redirect('error404')

    else:
        usuario = Usuario.objects.get(id=id_user)
        grupo_familiar = ''
        integrantes_grupo_familiar =''

        if usuario.rol.nombre == 'Beneficiario':#para obtener los datos de grupo familiar 
            beneficiario = Beneficiario.objects.get(usuario=usuario.id)
            grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
            integrantes_grupo_familiar = IntegranteGrupoFamiliar.objects.filter(grupo_familiar=grupo_familiar.id)
            
        if request.method == 'GET':
            context = {
                    'usuario':  usuario,
                    'grupo_familiar' : grupo_familiar,
                    'integrantes_grupo_familiar' : integrantes_grupo_familiar,
                    }
            return render(request, 'mi_perfil.html', context)



def editarPerfil(request, id_user):
    if 'usuario' not in request.session:
        return redirect('error404')

    if request.session['usuario']['id']!=id_user:
        return redirect('error404')

    usuario = Usuario.objects.get(id=id_user)
    grupo_familiar = ''
    integrantes_grupo_familiar =''
    beneficiario = ''

    if usuario.rol.nombre == 'Beneficiario':#para obtener los datos de grupo familiar 
        beneficiario = Beneficiario.objects.get(usuario=usuario.id)
        grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
        integrantes_grupo_familiar = IntegranteGrupoFamiliar.objects.filter(grupo_familiar=grupo_familiar.id)
        
    if request.method == 'GET':
        context = {
                'usuario':  usuario,
                'grupo_familiar' : grupo_familiar,
                'integrantes_grupo_familiar' : integrantes_grupo_familiar,
                }
        return render(request, 'editar_perfil.html', context)

    elif request.method == 'POST':
        errors = Usuario.objects.validador_basico(request.POST)

        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(editarPerfil, id_user)

        #si rol no beneficiario
        if usuario.rol.nombre != 'Beneficiario':
            usuario.nombres = request.POST['registro_nombres']
            usuario.apellido_paterno = request.POST['registro_ap_paterno']
            usuario.apellido_materno = request.POST['registro_ap_materno']
            #usuario.imagen = imagen_usuario,
            usuario.celular = request.POST['registro_celular']
            usuario.email = request.POST['registro_email'] 
            usuario.save()
            messages.success(request, f"Perfil editado con exito.")

        #si el rol es beneficiario
        if  usuario.rol.nombre == 'Beneficiario':
            errors = GrupoFamiliar.objects.validador_basico(request.POST)
            if len(errors) > 0:
                for key, value in errors.items():
                    messages.error(request, value);
                return redirect(editarPerfil, id_user)

            if not grupo_familiar.rsh_archivo: 
                if request.FILES.get('rsh_pdf'):
                    rsh_beneficiario = request.FILES['rsh_pdf']

                else:
                    rsh_beneficiario = ''
            else:
                if request.FILES.get('rsh_pdf'):
                    rsh_beneficiario = request.FILES['rsh_pdf']

                else:
                    rsh_beneficiario = grupo_familiar.rsh_archivo
                
            usuario.nombres = request.POST['registro_nombres']
            usuario.apellido_paterno = request.POST['registro_ap_paterno']
            usuario.apellido_materno = request.POST['registro_ap_materno']
            usuario.celular = request.POST['registro_celular']
            usuario.email = request.POST['registro_email']
            grupo_familiar.calif_soc_eco = request.POST['rsh_calificacion']
            grupo_familiar.direccion = request.POST['rsh_direccion']
            grupo_familiar.rsh_archivo =  rsh_beneficiario
            usuario.save()
            grupo_familiar.save()
            messages.success(request, f"Perfil editado con exito.")

    return redirect(miPerfil, id_user)



def cambiarContrasena(request, id_user):
    if 'usuario' not in request.session:
        return redirect('error404')
    
    if request.session['usuario']['id']!=id_user:
        return redirect('error404')

    if request.method == 'GET':
        return render(request, 'cambiar_contrasena.html')

    elif request.method == 'POST':
        usuario = Usuario.objects.get(id=id_user)
        if bcrypt.checkpw(request.POST['contrasena_actual'].encode(), usuario.contrasena.encode()):
            if request.POST['contrasena_segura'] == 'segura':
                if request.POST['contrasena_nueva'] == request.POST['contrasena_confirmacion']:
                    usuario.contrasena = bcrypt.hashpw(request.POST['contrasena_nueva'].encode(), bcrypt.gensalt()).decode()
                    usuario.save()
                    sendCambioContrasenaMail(usuario)
                    messages.success(request, f"Contraseña cambiada con éxito, se ha enviado un correo a { usuario.email } con la confirmación.")
                else:
                    messages.error(request, f"Las contraseñas nueva y su confirmación no son iguales.")
                    return redirect(cambiarContrasena, id_user)
            else:
                messages.error(request, f"La contraseña ingresada no es segura, ingrese una nueva contraseña.")
                return redirect(cambiarContrasena, id_user)       

        else:
            messages.error(request, f"La contraseña ingresada no coincide con la actual.")
            return redirect(cambiarContrasena, id_user)       
    
    return redirect(miPerfil, id_user)



@loginRequired
def precioGas(request):
    precio = PrecioGas.objects.get(estado=1)
    context = {
                'precio_gas' : precio,     
        }
    if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
        return render(request, 'admin/configuracion/precio_gas.html', context)
    elif request.session['usuario']['rol'] == 'Asistente':
        return render(request, 'asistente/configuracion/precio_gas.html', context)
    else:
        return redirect('error404')


@loginRequired
def nuevoPrecio(request):
    precio_actual = 0
    if(PrecioGas.objects.all()):
        precio_actual = PrecioGas.objects.get(estado=1)

    if request.method == 'GET':
        context = {
                'fecha': datetime.date.today(),
                'precio_actual': precio_actual
                }
        if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':       
            return render(request, 'admin/configuracion/nuevo_precio_gas.html', context)
        else:
            return redirect('error404')


    elif request.method == 'POST':
        errors = PrecioGas.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevoPrecio)
        
        else:
            precio = quitarMiles(request.POST['nuevo_precio'])
            if(not PrecioGas.objects.all()):
                usuario = Usuario.objects.get(id=request.session['usuario']['id'])
                nuevo_precio = PrecioGas.objects.create(
                                                precio = precio,
                                                usuario = usuario,
                                                estado = 1
                                                )            
                messages.success(request, f"Nuevo precio registrado con exito.")

            else:
                precio_vigente = PrecioGas.objects.get(estado=1)
                precio_vigente.precio = precio
                precio_vigente.usuario = Usuario.objects.get(id=request.session['usuario']['id'])
                precio_vigente.save()
                messages.success(request, f"Precio actualizado con exito.") 

            
        return redirect(precioGas)



@loginRequired
def descuentoAplicable(request):
    descuentos = DescuentoAplicable.objects.all()
    context = {
            'descuentos' : descuentos,     
    }
    if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
        return render(request, 'admin/configuracion/descuento_aplicable.html', context)
    elif request.session['usuario']['rol'] == 'Asistente':
        return render(request, 'asistente/configuracion/descuento_aplicable.html', context)
    else:
        return redirect('error404')


@loginRequired
def nuevoDescuento(request):
    if request.method == 'GET':
        if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
            return render(request, 'admin/configuracion/nuevo_descuento.html')
        else:
            return redirect('error404')

    elif request.method == 'POST':
        errors = DescuentoAplicable.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevoDescuento)
        
        else:
            usuario = Usuario.objects.get(id=request.session['usuario']['id'])
            nuevo_descuento = DescuentoAplicable.objects.create(
                                            calificacion_base = request.POST['descuento_base'],
                                            calificacion_tope = request.POST['descuento_tope'],
                                            descuento = request.POST['descuento_porcentaje'],
                                            usuario = usuario
                                            )            
            messages.success(request, f"Nuevo descuento registrado con exito.")
            
    return redirect(descuentoAplicable)



def editarDescuento(request, id_descuento):
    if 'usuario' not in request.session:
        return redirect('error404')

    descuento = DescuentoAplicable.objects.get(id=id_descuento)
    if request.method == 'GET':
        context = {
                'descuento': descuento
                }
        if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
            return render(request, 'admin/configuracion/editar_descuento.html', context)
        else:
            return redirect('error404')

    elif request.method == 'POST':
        errors = DescuentoAplicable.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(editarDescuento, descuento.id)
        
        else:
            descuento.calificacion_base = request.POST['descuento_base']
            descuento.calificacion_tope = request.POST['descuento_tope']
            descuento.descuento = request.POST['descuento_porcentaje']
            descuento.save()
            messages.success(request, f"Descuento actualizado con exito.")

    return redirect('descuentoAplicable')



def eliminarDescuento(request, id_descuento):
    if 'usuario' not in request.session:
            return redirect('error404')
    if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
        descuento = DescuentoAplicable.objects.get(id=id_descuento)
        descuento.delete()
        return redirect(descuentoAplicable)
    else:
        return redirect('error404')

    

@loginRequired
def cantConvenios(request):
    cant_convenios = CantidadConvenio.objects.get(estado=1)
    context = {
            'cant_convenios' : cant_convenios,     
    }
    if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
        return render(request, 'admin/configuracion/cantidad_convenios.html', context)
    elif request.session['usuario']['rol'] == 'Asistente':
        return render(request, 'asistente/configuracion/cantidad_convenios.html', context)
    else:
        return redirect('error404')


@loginRequired 
def nuevoCantConvenios(request):
    cantidad_actual = 0
    if request.method == 'GET':
        if(CantidadConvenio.objects.all()):
            cantidad_actual = CantidadConvenio.objects.get(estado=1)

        context = {
                'fecha': datetime.date.today(),
                'cantidad_actual':cantidad_actual
                }
        if request.session['usuario']['rol'] == 'Administrador' or request.session['usuario']['rol'] == 'Director':
            return render(request, 'admin/configuracion/nuevo_cantidad_convenios.html', context)
        else:
            return redirect('error404')

    elif request.method == 'POST':
        errors = CantidadConvenio.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(nuevoCantConvenios)
        
        else:
            if(not CantidadConvenio.objects.all()):#si no exiten
                usuario = Usuario.objects.get(id=request.session['usuario']['id'])
                nueva_cantidad = CantidadConvenio.objects.create(
                                                                cantidad_convenios = request.POST['cant_convenios'],
                                                                usuario = usuario,
                                                                estado = 1
                                                                )            
                messages.success(request, f"Nueva cantidad de convenios registrada con éxito.")

            else:
                cantidad_vigente = CantidadConvenio.objects.get(estado=1)
                cantidad_vigente.cantidad_convenios = request.POST['cant_convenios']
                cantidad_vigente.usuario = Usuario.objects.get(id=request.session['usuario']['id'])
                cantidad_vigente.save()
                messages.success(request, f"Cantidad de convenios actualizada con exito.") 

            
        return redirect(cantConvenios)




@loginRequired
def solicitudes(request):
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    solicitudes = Solicitud.objects.all()
    context = {
            'solicitudes' : solicitudes,     
    }
    return render(request, 'admin/solicitudes/solicitudes.html', context)



def verSolicitud(request,id_solicitud):
    if 'usuario' not in request.session:
            return redirect('error404')
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')
    
    solicitud = Solicitud.objects.get(id=id_solicitud)
    beneficiario = Beneficiario.objects.get(id=solicitud.beneficiario.id)
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    estado_solicitud = ''
    cant_convenios = cantConveniosSolicitados(beneficiario.id)
    cant_max_convenios = CantidadConvenio.objects.get(estado=1) 

    if solicitud.estado == 0 :
        estado_solicitud = 'Pendiente' 
    elif solicitud.estado == 1:
        estado_solicitud = 'Aceptada'
    elif solicitud.estado == 2:
        estado_solicitud = 'Rechazada'
    elif solicitud.estado == 3:
        estado_solicitud = 'Convenio generado'
    
    
    if request.method == 'GET':
        context = {
                'solicitud': solicitud,
                'beneficiario':beneficiario,
                'grupo_familiar': grupo_familiar,
                'cant_convenios' : cant_convenios,
                'estado_solicitud' : estado_solicitud,
                'cant_max_convenios' : cant_max_convenios.cantidad_convenios,
                }
        return render(request, 'admin/solicitudes/ver_solicitud.html', context)




def rechazarSolicitud(request,id_solicitud):
    if 'usuario' not in request.session:
            return redirect('error404')
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    solicitud = Solicitud.objects.get(id=id_solicitud)

    if solicitud.estado != 0:
        messages.error(request, f"No es posible rechazar la solicitud.")
        return redirect(verSolicitud, id_solicitud)

    beneficiario = Beneficiario.objects.get(id=solicitud.beneficiario.id)
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    usuario = Usuario.objects.get(id=beneficiario.usuario.id)
    estado_solicitud = ''
    cant_convenios = cantConveniosSolicitados(beneficiario.id)
    cant_max_convenios = CantidadConvenio.objects.get(estado=1) 

    if solicitud.estado == 0 :
        estado_solicitud = 'Pendiente' 
    elif solicitud.estado == 1:
        estado_solicitud = 'Aceptada'
    elif solicitud.estado == 2:
        estado_solicitud = 'Rechazada'
    elif solicitud.estado == 3:
        estado_solicitud = 'Convenio generado'

    if request.method == 'GET':
        messages.success(request, f"Debe ingresar una observación de rechazo.")
        context = {
                'solicitud': solicitud,
                'beneficiario':beneficiario,
                'grupo_familiar': grupo_familiar,
                'cant_convenios' : cant_convenios,
                'estado_solicitud' : estado_solicitud,
                'cant_max_convenios' : cant_max_convenios.cantidad_convenios,
                }
        return render(request, 'admin/solicitudes/rechazar_solicitud.html', context)

    elif request.method == 'POST':
        errors = Solicitud.objects.validador_observacion(request.POST)
        request.session['observacion_solicitud'] =  request.POST['observacion_solicitud']
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(rechazarSolicitud)
        else:
            solicitud.usuario = Usuario.objects.get(id=request.session['usuario']['id'])
            solicitud.observacion = request.POST['observacion_solicitud']
            solicitud.estado = 2
            solicitud.save()
            sendCambioEstadoSolicitud(usuario, 'Rechazada', solicitud.created_at)
            messages.success(request, f"La solicitud a sido rechazada.")
    
    del request.session['observacion_solicitud']        
    return redirect(solicitudes)




def aceptarSolicitud(request,id_solicitud):
    if 'usuario' not in request.session:
            return redirect('error404')
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')
    
    solicitud = Solicitud.objects.get(id=id_solicitud)

    if solicitud.estado != 0:
        messages.error(request, f"No es posible aceptar la solicitud.")
        return redirect(verSolicitud, id_solicitud)

    beneficiario = Beneficiario.objects.get(id=solicitud.beneficiario.id)
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    usuario = Usuario.objects.get(id=beneficiario.usuario.id)
    estado_solicitud = ''
    cant_convenios = cantConveniosSolicitados(beneficiario.id)
    cant_max_convenios = CantidadConvenio.objects.get(estado=1) 

    if solicitud.estado == 0 :
        estado_solicitud = 'Pendiente' 
    elif solicitud.estado == 1:
        estado_solicitud = 'Aceptada'
    elif solicitud.estado == 2:
        estado_solicitud = 'Rechazada'
    elif solicitud.estado == 3:
        estado_solicitud = 'Convenio generado'

    if request.method == 'GET':
        context = {
                'solicitud': solicitud,
                'beneficiario':beneficiario,
                'grupo_familiar': grupo_familiar,
                'cant_convenios' : cant_convenios,
                'estado_solicitud' : estado_solicitud,
                'cant_max_convenios' : cant_max_convenios.cantidad_convenios,
                }
        return render(request, 'admin/solicitudes/aceptar_solicitud.html', context)

    elif request.method == 'POST':
        if cant_convenios >= cant_max_convenios.cantidad_convenios:
            messages.error(request, f"El beneficiario ya cumplió la cantidad máxima de convenios por mes.")
            return redirect(aceptarSolicitud, id_solicitud)

        errors = Solicitud.objects.validador_observacion(request.POST)
        request.session['observacion_solicitud'] =  request.POST['observacion_solicitud']
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(aceptarSolicitud, id_solicitud)
        else:
            solicitud.usuario = Usuario.objects.get(id=request.session['usuario']['id'])
            solicitud.observacion = request.POST['observacion_solicitud']
            solicitud.estado = 1
            solicitud.save()
            sendCambioEstadoSolicitud(usuario, 'Aceptada', solicitud.created_at)
            messages.success(request, f"La solicitud a sido aceptada.")
    
    del request.session['observacion_solicitud']        
    return redirect(solicitudes)




def generarConvenio(request,id_solicitud):
    if 'usuario' not in request.session:
            return redirect('error404')
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    solicitud = Solicitud.objects.get(id=id_solicitud)
    beneficiario = Beneficiario.objects.get(id=solicitud.beneficiario.id)
    usuario = Usuario.objects.get(id=request.session['usuario']['id'])
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    precio_gas = PrecioGas.objects.get(estado=1)
    precio_gas_final = ''
    descuento_aplicado = ''
    descuentos = DescuentoAplicable.objects.all()

    
    cant_convenios = cantConveniosSolicitados(beneficiario.id)
    cant_max_convenios = CantidadConvenio.objects.get(estado=1) 
    if cant_convenios >= cant_max_convenios.cantidad_convenios:
        messages.error(request, f"El beneficiario ya cumplió la cantidad máxima de convenios por mes.")
        return redirect(solicitudes)


    for descuento in descuentos:
        if grupo_familiar.calif_soc_eco >= descuento.calificacion_base and grupo_familiar.calif_soc_eco <= descuento.calificacion_tope:
            descuento_aplicado = descuento.descuento
            precio_gas_final = int(precio_gas.precio - (precio_gas.precio * (descuento_aplicado/100)))


    new_convenio = Convenio.objects.create(
                                            usuario = usuario,
                                            beneficiario = beneficiario,
                                            precio = precio_gas_final,
                                            descuento_aplicado = descuento_aplicado,
                                            estado = 0
                                            )
    solicitud.estado = 3
    solicitud.save()
    sendCambioEstadoSolicitud(beneficiario.usuario, 'Convenio Generado', solicitud.created_at)
    messages.success(request, f"Convenio generado con éxito.")

    return redirect(solicitudes)




def cantConveniosSolicitados(id_beneficiario):
    beneficiario = Beneficiario.objects.get(id=id_beneficiario)
    convenios = Convenio.objects.filter(beneficiario=beneficiario.id)
    year_actual = int(format(datetime.datetime.now().year))
    mes_actual = int(format(datetime.datetime.now().month))
    cant_convenios = 0


    for convenio in convenios:
        if int(convenio.created_at.year) == year_actual and int(convenio.created_at.month) == mes_actual:
            cant_convenios+=1
    return cant_convenios




@loginRequired
def misSolicitudes(request):
    if not request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    beneficiario = Beneficiario.objects.get(usuario=request.session['usuario']['id'])
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    try:
        solicitudes = Solicitud.objects.filter(beneficiario=beneficiario.id)
    except ZeroDivisionError:
        print("No existen solicitudes asociadas al Beneficiario.")

    context = {
            'solicitudes' : solicitudes,     
    }
    if request.session['usuario']['rol'] == 'Beneficiario':
        return render(request, 'beneficiario/solicitudes/mis_solicitudes.html', context)



@loginRequired
def nuevaSolicitud(request):
    if not request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    beneficiario = Beneficiario.objects.get(usuario=request.session['usuario']['id'])
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    if request.method == 'GET':
        context = {
                'fecha': datetime.date.today(),
                'grupo_familiar': grupo_familiar,
                }
        return render(request, 'beneficiario/solicitudes/nueva_solicitud.html', context)
    
    elif request.method == 'POST':
        errors = Solicitud.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevaSolicitud)
        
        else:
            nueva_solicitud = Solicitud.objects.create(beneficiario = beneficiario)            
            messages.success(request, f"Nueva solicitud registrada con éxito.")
        
    return redirect(misSolicitudes)



def editarSolicitud(request, id_solicitud):
    if 'usuario' not in request.session:
            return redirect('error404')
    if not request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    beneficiario = Beneficiario.objects.get(usuario=request.session['usuario']['id'])
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    solicitud = Solicitud.objects.get(id=id_solicitud)
    if request.method == 'GET':
        now = datetime.datetime.now()
        context = {
                'solicitud': solicitud,
                'fecha':  now,
                'grupo_familiar': grupo_familiar,
                }
        return render(request, 'beneficiario/solicitudes/editar_solicitud.html', context)
    
    elif request.method == 'POST':
        errors = Solicitud.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevaSolicitud)
        
        else:
            solicitud.created_at =  datetime.datetime.now()
            solicitud.save()           
            messages.success(request, f"Solicitud actualizada con éxito.")
        
    return redirect(misSolicitudes)



def eliminarSolicitud(request, id_solicitud):
    if 'usuario' not in request.session:
            return redirect('error404')
    if not request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    solicitud = Solicitud.objects.get(id=id_solicitud)
    solicitud.delete()

    return redirect(misSolicitudes)
    


@loginRequired
def convenios(request):
    if request.session['usuario']['rol'] == 'Beneficiario':
        beneficiario = Beneficiario.objects.get(usuario=request.session['usuario']['id'])
        convenios = Convenio.objects.filter(beneficiario=beneficiario.id)
        print(f'Beneficiario {beneficiario.id}')
        context = {
                'convenios' : convenios,     
        }
        return render(request, 'beneficiario/convenios/mis_convenios.html', context)
    
    else:
        convenios = Convenio.objects.all()
        context = {
                'convenios' : convenios,     
        }
        return render(request, 'admin/convenios/convenios.html', context)





def convenioPdf(request,id_convenio,descargar):
    if 'usuario' not in request.session:
            return redirect('error404')
    convenio = Convenio.objects.get(id=id_convenio)
    cantidad_max_convenio = CantidadConvenio.objects.get(estado=1)
    template = get_template('admin/convenios/pdf_convenio.html')
    context = {
        'convenio' : convenio,
        'fecha' : datetime.date.today(),
        'cantidad_max_convenio': cantidad_max_convenio,
    }
    html = template.render(context)
    try:
        # Create a Django response object, and specify content_type as pdf
        filename = f'convenio_{id_convenio}'
        response = HttpResponse(content_type='application/pdf')
        if descargar == 1:
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        # create a pdf
        pisa_status = pisa.CreatePDF(html, dest=response)
        convenio.estado = 1
        convenio.save()
        return response
    except:
        pass
    return redirect(convenios)




@loginRequired
def nuevoConvenio(request):
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    if request.method == 'GET':
        context = {
                'fecha': datetime.date.today(),
                }
        return render(request, 'admin/convenios/nuevo_convenio.html', context)
    
    elif request.method == 'POST':
        errors = Convenio.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevoConvenio)
        
        else:
            rut_sin_dv = formRut(request.POST['rut'])
            try:
                usuario_beneficiario = Usuario.objects.get(rut=rut_sin_dv['rut'])
                beneficiario = Beneficiario.objects.get(usuario=usuario_beneficiario.id)
                cant_convenios = cantConveniosSolicitados(beneficiario.id)
                cant_max_convenios = CantidadConvenio.objects.get(estado=1) 
                if cant_convenios >= cant_max_convenios.cantidad_convenios:
                    messages.error(request, f"El beneficiario ya cumplió la cantidad máxima de convenios por mes.")
                    return redirect(nuevoConvenio)
            except Exception as e:           
                messages.error(request, f"El RUT {request.POST['rut']} no se encuentra registrado como beneficiario.")
                return redirect(nuevoConvenio) 

            grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
            precio_gas = PrecioGas.objects.get(estado=1)
            precio_gas_final = ''
            descuento_aplicado = ''
            descuentos = DescuentoAplicable.objects.all()

            for descuento in descuentos:
                if grupo_familiar.calif_soc_eco >= descuento.calificacion_base and grupo_familiar.calif_soc_eco <= descuento.calificacion_tope:
                    descuento_aplicado = descuento.descuento
                    precio_gas_final = int(precio_gas.precio - (precio_gas.precio * (descuento_aplicado/100)))


            new_convenio = Convenio.objects.create(
                                                    usuario = Usuario.objects.get(id=request.session['usuario']['id']),
                                                    beneficiario = beneficiario,
                                                    precio = precio_gas_final,
                                                    descuento_aplicado = descuento_aplicado,
                                                    estado = 0
                                                    )
            messages.success(request, f"Convenio registrado con éxito.")
        
    return redirect(convenios)




def editarConvenio(request, id_convenio):
    if 'usuario' not in request.session:
        return redirect('error404')
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    convenio = Convenio.objects.get(id=id_convenio)
    
    if request.method == 'GET':
        usuario = Usuario.objects.get(id=convenio.beneficiario.usuario.id)
        cantidad_max_convenio = CantidadConvenio.objects.get(estado=1)
        context = {
            'convenio' : convenio,
            'fecha' : datetime.date.today(),
            'cantidad_max_convenio': cantidad_max_convenio,
            'usuario_rut' : (f"{usuario.rut}-{usuario.dv}"),
        }
        return render(request, 'admin/convenios/editar_convenio.html', context)

    elif request.method == 'POST':
        if convenio.estado == 1:
            messages.error(request, f"No es posible editar el convenio, este se encuentra en proceso de pago.")
            return redirect(editarConvenio, id_convenio)
        else:
            convenio.created_at =  datetime.datetime.now()
            convenio.save()           
            messages.success(request, f"Convenio actualizado con éxito.")
            return redirect(convenios)
    



def verConvenio(request, id_convenio):
    if 'usuario' not in request.session:
            return redirect('error404')
    
    convenio = Convenio.objects.get(id=id_convenio)
    usuario = Usuario.objects.get(id=convenio.beneficiario.usuario.id)
    cantidad_max_convenio = CantidadConvenio.objects.get(estado=1)
    context = {
        'convenio' : convenio,
        'fecha' : datetime.date.today(),
        'cantidad_max_convenio': cantidad_max_convenio,
        'usuario_rut' : (f"{usuario.rut}-{usuario.dv}"),
    }
    if request.session['usuario']['rol'] == 'Beneficiario':
            return render(request, 'beneficiario/convenios/ver_convenio.html', context)

    return render(request, 'admin/convenios/ver_convenio.html', context)




def eliminarConvenio(request, id_convenio):
    if 'usuario' not in request.session:
                return redirect('error404')
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    convenio = Convenio.objects.get(id=id_convenio)
    
    if convenio.estado != 1:
        convenio.delete()
    else:
        messages.error(request, "No es posible eliminar el convenio, este se encuentra en proceso de pago.")

    return redirect(convenios)





def integrantesGrupoFamiliar(request, id_usuario_beneficiario):
    if 'usuario' not in request.session:
        return redirect('error404')
    beneficiario = Beneficiario.objects.get(usuario=id_usuario_beneficiario)
    grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)
    integrantes_grupo_familiar = IntegranteGrupoFamiliar.objects.filter(grupo_familiar=grupo_familiar.id)
        
    context = {
            'beneficiario': beneficiario,
            'usuario' : Usuario.objects.get(id=beneficiario.usuario.id),
            'grupo_familiar' : grupo_familiar,
            'integrantes_grupo_familiar' : integrantes_grupo_familiar,
            }
    
    return render(request, 'beneficiario/grupo_familiar/mi_grupo_familiar.html', context)





def nuevoIntegrante(request, id_usuario_beneficiario):
    if 'usuario' not in request.session:
        return redirect('error404')
    if request.method == 'GET':
        context = {
                'usuario' : Usuario.objects.get(id=id_usuario_beneficiario),
                }

        return render(request, 'beneficiario/grupo_familiar/nuevo_integrante.html', context)
    
    elif request.method == 'POST':
        rut_nuevo_registro = formRut(request.POST['rut_integrante'])
        errors = IntegranteGrupoFamiliar.objects.validador_basico(request.POST)
        #Variables de session para guardar los datos en caso de error el usuario no tenga que escribir todo
        request.session['nombres_integrante'] =  request.POST['nombres_integrante']
        request.session['ap_paterno_integrante'] = request.POST['ap_paterno_integrante']
        request.session['ap_materno_integrante'] = request.POST['ap_materno_integrante']
        request.session['rut_integrante'] = request.POST['rut_integrante']
        request.session['parentesco'] = request.POST['parentesco']
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(nuevoIntegrante, id_usuario_beneficiario)
        
        else:
            beneficiario = Beneficiario.objects.get(usuario=id_usuario_beneficiario)
            grupo_familiar = GrupoFamiliar.objects.get(id=beneficiario.grupo_familiar.id)

            new_integrante = IntegranteGrupoFamiliar.objects.create(
                                        nombres = request.POST['nombres_integrante'],
                                        apellido_paterno = request.POST['ap_paterno_integrante'],
                                        apellido_materno = request.POST['ap_materno_integrante'],
                                        rut = int(rut_nuevo_registro['rut']),
                                        dv = rut_nuevo_registro['dv'],
                                        parentesco = request.POST['parentesco'],
                                        grupo_familiar = grupo_familiar,
                                        )
            
            messages.success(request, f"Nuevo integrante registrado con exito.")
        delVaSessionIntegrante(request)
        return redirect(integrantesGrupoFamiliar, id_usuario_beneficiario)




def editarIntegrante(request,id_integrante):
    if 'usuario' not in request.session:
        return redirect('error404')
    
    integrante = IntegranteGrupoFamiliar.objects.get(id=id_integrante)
    beneficiario = Beneficiario.objects.get(grupo_familiar=integrante.grupo_familiar.id)
    usuario_beneficiario = Usuario.objects.get(id=beneficiario.usuario.id)

    if request.method == 'GET':
        context = {
                'usuario' : usuario_beneficiario,
                'integrante' : integrante,
                'integrante_rut' : (f"{integrante.rut}-{integrante.dv}"),
                }
        return render(request, 'beneficiario/grupo_familiar/editar_integrante.html', context)

    elif request.method == 'POST':
        errors = IntegranteGrupoFamiliar.objects.validador_basico(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(editarIntegrante,id_integrante)
        
        else:
            integrante.nombres = request.POST['nombres_integrante']
            integrante.apellido_paterno = request.POST['ap_paterno_integrante']
            integrante.apellido_materno = request.POST['ap_materno_integrante']
            integrante.parentesco = request.POST['parentesco']
            integrante.save()
            messages.success(request, f"Integrante editado con exito.")
            return redirect(integrantesGrupoFamiliar, usuario_beneficiario.id)




def eliminarIntegrante(request,id_integrante):
    if 'usuario' not in request.session:
                return redirect('error404')

    integrante = IntegranteGrupoFamiliar.objects.get(id=id_integrante)
    integrante.delete()

    beneficiario = Beneficiario.objects.get(grupo_familiar=integrante.grupo_familiar.id)
    usuario_beneficiario = Usuario.objects.get(id=beneficiario.usuario.id)
    return redirect(integrantesGrupoFamiliar, usuario_beneficiario.id)




@loginRequired
def informeCantConvenios(request):
    if request.session['usuario']['rol'] == 'Beneficiario':
        return redirect('error404')

    if request.method == 'GET':
        return render(request, 'admin/informes/cantidad_de_convenios.html')
    
    elif request.method == 'POST':
        errors = Convenio.objects.validador_cant_convenios(request.POST)
        
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value);
            return redirect(informeCantConvenios)

        else:
            fecha_inicial = request.POST['fecha_inicial']
            fecha_termino = request.POST['fecha_termino']
            hoy = datetime.date.today()


            convenios = Convenio.objects.filter(created_at__range=(fecha_inicial,fecha_termino))
            cant = convenios.count()
            context = {
                'convenios' : convenios,
                'cant' : cant,
            }
            if request.session['usuario']['rol'] == 'Beneficiario':
                    return redirect('error404')
            else:
                return render(request, 'admin/informes/descargar_informe.html', context)




def error404(request, exception=None):
    return render(request, '404.html')




def recuperarContrasena(request):
    if request.method == 'GET':
        return render(request, 'recuperar_contrasena.html')

    elif request.method == 'POST':
        if Usuario.objects.get(rut=request.POST['rut_login']):
            usuario = Usuario.objects.get(rut=request.POST['rut_login'])
            if usuario.estado == 0:
                    messages.error(request, "Usuario inactivo, contacte al administrador de la aplicación.")

            else:
                new_password = crearPass()
                password_encryp = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                usuario.contrasena = password_encryp
                usuario.save()
                messages.success(request, f"Se ha enviado una nueva contraseña al correo {usuario.email}.")
                sendTempPasswordMail(usuario, new_password)
                

    return redirect("/")



def crearPass():
    simbolos = ['!','@','#','$','%','&','>','<','*']
    todos = list(string.ascii_letters)+list(string.digits)+simbolos
    contrasena = ''.join(rd.sample(todos, 6))

    return contrasena



def quitarMiles(numero):
    numero = re.sub("\.","",numero)
    return int(numero)




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
                                    'Bienvenida a la aplicación DIDECO',
                                    'DIDECO COELEMU',
                                    settings.EMAIL_HOST_USER,
                                    [user.email],#destinatarios
                                    #CC=[], se puede definir con copia a 
                                )
    email.attach_alternative(content, 'text/html')#agregar el contenido al correo
    email.send()



def sendTempPasswordMail(user, password):
    context = {
        'nombre'  : f"{user}",
        'rut'     : user.rut,
        'password': password,
        'mail'    : user.email
    }
    template = get_template('correos/contrasena_temporal.html')
    content = template.render(context)
    email = EmailMultiAlternatives(
                                    'Contraseña Temporal',
                                    'DIDECO COELEMU',
                                    settings.EMAIL_HOST_USER,
                                    [user.email],#destinatarios
                                    #CC=[], se puede definir con copia a 
                                )
    email.attach_alternative(content, 'text/html')#agregar el contenido al correo
    email.send()



def sendCambioContrasenaMail(user):
    context = {
        'nombre'  : f"{user}",
        'mail'    : user.email
    }
    template = get_template('correos/cambio_contrasena.html')
    content = template.render(context)
    email = EmailMultiAlternatives(
                                    'Cambio de contraseña',
                                    'DIDECO COELEMU',
                                    settings.EMAIL_HOST_USER,
                                    [user.email],#destinatarios
                                    #CC=[], se puede definir con copia a 
                                )
    email.attach_alternative(content, 'text/html')#agregar el contenido al correo
    email.send()



def sendCambioEstadoSolicitud(user, nuevo_estado, fecha_solicitud):
    context = {
        'nombre'  : f"{user}",
        'mail'    : user.email,
        'estado'   : nuevo_estado,
        'fecha_solicitud' : fecha_solicitud,
    }
    template = get_template('correos/cambio_estado_solicitud.html')
    content = template.render(context)
    email = EmailMultiAlternatives(
                                    'Cambio de estado solicitud',
                                    'DIDECO COELEMU',
                                    settings.EMAIL_HOST_USER,
                                    [user.email],#destinatarios
                                    #CC=[], se puede definir con copia a 
                                )
    email.attach_alternative(content, 'text/html')#agregar el contenido al correo, en plantillas correo
    email.send()





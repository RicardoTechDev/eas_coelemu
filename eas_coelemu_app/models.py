from django.db import models
from itertools import cycle
import re

class UsuarioManager(models.Manager):
    def formRut(self, rut_sin_form):
        rut = ''
        dv = ''
        
        for indice in range(len(rut_sin_form)):
            if(rut_sin_form[indice]=="-"):
                if rut_sin_form[indice+1] == 'k' or rut_sin_form[indice+1] == 'K':
                    dv = rut_sin_form[indice+1].upper()
                    break
                dv = rut_sin_form[indice+1]
                break
            else:
                rut += rut_sin_form[indice]

        rut_form ={
            'rut' : rut,
            'dv' : dv
        }

        return rut_form



    def digito_verificador(self, rut):
        reversed_digits = map(int, reversed(str(rut)))
        factors = cycle(range(2, 8))
        s = sum(d * f for d, f in zip(reversed_digits, factors))
        if ((-s) % 11)==10:
            return 'K'
        
        return (-s) % 11



    def validador_basico(self, postData):
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        SOLO_LETRAS = re.compile(r'^[a-zA-Z. ]+$')

        errors = {}

        rut = self.formRut(postData['registro_rut'])
        dv = str(self.digito_verificador(rut['rut']))#El digito verificador pueder ser un número o k

        if len(postData['registro_nombres']) < 3:
            errors['nombres_len'] = "Los nombres deben tener al menos 3 caracteres de largo."
        
        if not SOLO_LETRAS.match(postData['registro_nombres']):
            errors['solo_letras_nombres'] = "Los nombres deben contener solo letras."

        if len(postData['registro_ap_paterno']) < 3:
            errors['ap_paternon'] = "El apellido paterno debe tener al menos 3 caracteres de largo."

        if not SOLO_LETRAS.match(postData['registro_ap_paterno']):
            errors['solo_letras_ap_paterno'] = "El apellido paterno debe contener solo letras."

        if len(postData['registro_ap_materno']) < 3:
            errors['ap_paternon'] = "El apellido paterno debe tener al menos 3 caracteres de largo."

        if not SOLO_LETRAS.match(postData['registro_ap_paterno']):
            errors['solo_letras_ap_materno'] = "El apellido materno debe contener solo letras."

        if postData['registro_rut'] == '':
            errors['rut_vacio'] = "Debe ingresar el RUT."
        
        if  rut['dv']!=dv:
            errors['rut_incorrecto'] = "El RUT ingresado no es valido."
        
        if not EMAIL_REGEX.match(postData['registro_email']):
            errors['fail_email'] = "Correo invalido."


        return errors


class Rol(models.Model):
    nombre = models.CharField(max_length=13)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.nombre}"


class Usuario(models.Model):
    nombres = models.CharField(max_length=255) 
    apellido_paterno = models.CharField(max_length=255)
    apellido_materno = models.CharField(max_length=255)
    rut = models.IntegerField()
    dv = models.CharField(max_length=1)
    imagen = models.ImageField(upload_to="usuarios/perfil", null=True, blank=True)
    celular = models.CharField(max_length=9)
    email = models.EmailField()
    contrasena = models.CharField(max_length=8)
    rol = models.ForeignKey(Rol, related_name="usuarios", on_delete = models.CASCADE)#related_name="usuarios"
    estado = models.IntegerField()#Actvivo(1) o Inactivo(0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UsuarioManager()

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"


    def __repr__(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

    class Meta:
        #verbose_name = "usuarios"
        ordering = ["-created_at"]



class PrecioGas(models.Model):
    precio = models.IntegerField()
    usuario = models.ForeignKey(Usuario, related_name="preciogas", on_delete = models.CASCADE)#almacenará el ultimo usuario que modifico
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DescuentoAplicable(models.Model):#establece que descuento se aplicará según el % de la ficha
    calificacion = models.IntegerField()
    decuento = models.IntegerField()
    usuario = models.ForeignKey(Usuario, related_name="descuentoaplicable", on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
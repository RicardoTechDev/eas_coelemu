from pyexpat import model
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
            
        if postData['registro_rol'] == 'Seleccionar Rol':
            errors['fail_rol'] = "Debe selecionar un Rol para el usuario."

        return errors



class PrecioGasManager(models.Manager):
    def validador_basico(self, postData):
        errors = {}

        if len(postData['nuevo_precio']) == 0:
            errors['nuevo_precio_len'] = "El precio no puede estar vacio."

        if postData['nuevo_precio']:
            try:
                valor = float(postData['nuevo_precio'])#solo lo usamos para atrapar en error
            except Exception as e:
                errors['nuevo_precio_no_numero'] = "Solo puede ingresar números."

        return errors


class DescuentoAplicableManager(models.Manager):
    def validador_basico(self, postData):
        SOLO_NUMEROS = re.compile(r'^[0-9.]+$')  

        errors = {}
        #errores calificación base
        if postData['descuento_base']:
            try:
                if int(postData['descuento_base']) > 100:
                    errors['descuento_base_cien'] = "El porcentaje base no puede ser mayor a 100." 

                if int(postData['descuento_base']) > int(postData['descuento_tope']):
                    errors['base_mayor_tope'] = "El porcentaje base no puede ser mayor al tope."
                
                if postData['descuento_base'] == postData['descuento_tope']:
                    errors['base_mayor_tope'] = "El porcentaje base no puede ser mayor al tope."

            except Exception as e:
                errors['descuento_base_numero_entero'] = "Debe ingresar solo números enteros en Calificación base."
        
        if len(postData['descuento_base']) == 0:
            errors['descuento_base_len'] = "Debe ingresar el porcentaje base."

        #errores calificación tope
        if postData['descuento_tope']:
            try:
                if int(postData['descuento_tope']) > 100:
                    errors['descuento_tope_cien'] = "El porcentaje tope no puede ser mayor a 100." 
                
                if postData['descuento_tope'] == '0':
                    errors['descuento_tope_cero'] = "El porcentaje tope no puede ser cero." 

                #if not SOLO_NUMEROS.match(postData['descuento_tope']):
                #   errors['descuento_tope_numero'] = "Debe ingresar solo números en Calificación tope."

            except Exception as e:
                errors['descuento_tope_numero_entero'] = "Debe ingresar solo números enteros en Calificación tope."

        if len(postData['descuento_tope']) == 0:
            errors['descuento_tope_len'] = "Debe ingresar el porcentaje tope." 

        #errores calificación porcentaje descuento
        if postData['descuento_porcentaje']:
            try:
                if int(postData['descuento_porcentaje']) > 100:
                    errors['descuento_porcentaje_cero'] = "El porcentaje de descuento no puede ser mayor a 100." 
            except Exception as e:
                errors['descuento_porcentaje_entero'] = "Debe ingresar solo números enteros en Descuento aplicable."

        if len(postData['descuento_porcentaje']) == 0:
            errors['descuento_porcentaje_len'] = "Debe ingresar el porcentaje de descuento."

        return errors


class CantidadConvenioManager(models.Manager):
    def validador_basico(self, postData):
        SOLO_NUMEROS = re.compile(r'^[0-9.]+$')  

        errors = {}
        #errores calificación base
        if postData['cant_convenios']:
            try:
                if int(postData['cant_convenios']) > 100:
                    errors['cant_convenios_cien'] = "No es posible superar los 100 convenios mensuales." 


            except Exception as e:
                errors['cant_convenios_numero_entero'] = "Debe ingresar solo números enteros en la cantidad de convenios."


        return errors


class GrupoFamiliarManager(models.Manager):
    def validador_basico(self, postData):
        errors = {}

        if len(postData['rsh_direccion']) == 0:
            errors['rsh_direccion_len'] = "Debe ingresar la dirección del RHS."

        if len(postData['rsh_calificacion']) == 0:
            errors['rsh_calificacion_len'] = "Debe ingresar la calificación socioeconómica del RHS."

        if postData['rsh_calificacion']:
            try:
                if int(postData['rsh_calificacion']) < 0 or int(postData['rsh_calificacion']) > 100:
                    errors['rsh_calificacion_menor'] = "Debe ingresar un calificación socioeconómica entre 0 y 100."
            except Exception as e:
                errors['rsh_calificacion'] = "Debe ingresar solo números enteros en calificación socioeconómica."

        
        

        return errors

class IntegranteGrupoFamiliarManager(models.Manager):
    def validador_basico(self, postData):
        errors = {}

        #if len(postData['registro_nombres']) < 3:
        #   errors['nombres_len'] = "Los nombres deben tener al menos 3 caracteres de largo."

        return errors


class BeneficiarioManager(models.Manager):
    def validador_basico(self, postData):
        errors = {}

        #if len(postData['registro_nombres']) < 3:
        #   errors['nombres_len'] = "Los nombres deben tener al menos 3 caracteres de largo."

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
    estado = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = PrecioGasManager()

    class Meta:
        ordering = ["-created_at"]


class DescuentoAplicable(models.Model):#establece que descuento se aplicará según el % de la ficha
    calificacion_base = models.IntegerField()
    calificacion_tope = models.IntegerField()
    descuento = models.IntegerField()
    usuario = models.ForeignKey(Usuario, related_name="descuentoaplicable", on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = DescuentoAplicableManager()


class CantidadConvenio(models.Model):
    cantidad_convenios = models.IntegerField()
    usuario = models.ForeignKey(Usuario, related_name="cantidadconvenio", on_delete = models.CASCADE)
    estado = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CantidadConvenioManager()


class GrupoFamiliar(models.Model):   
    calif_soc_eco = models.IntegerField()
    direccion = models.CharField(max_length=200)
    rsh_archivo = models.FileField(upload_to="grupo_familiar/", null=True, blank=True)#Archivo Pdf Registro Social de Hogares 
    estado = models.IntegerField()#Actvivo(1) o Inactivo(0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = GrupoFamiliarManager()


class IntegranteGrupoFamiliar(models.Model):
    nombres = models.CharField(max_length=255) 
    apellido_paterno = models.CharField(max_length=255)
    apellido_materno = models.CharField(max_length=255)
    rut = models.IntegerField()
    dv = models.CharField(max_length=1)
    parentesco = models.CharField(max_length=25)#con el beneficiario
    grupo_familiar = models.ForeignKey(GrupoFamiliar, related_name="integrante", on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = IntegranteGrupoFamiliarManager()


class Beneficiario(models.Model):
    grupo_familiar = models.ForeignKey(GrupoFamiliar, related_name="beneficiario", on_delete = models.CASCADE)
    usuario = models.ForeignKey(Usuario, related_name="beneficiario", on_delete = models.CASCADE)#Usuario asociado al beneficiario 
    estado = models.IntegerField()#Actvivo(1) o Inactivo(0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = BeneficiarioManager()
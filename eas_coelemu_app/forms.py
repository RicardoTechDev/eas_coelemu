from dataclasses import fields
from django.forms import ModelForm
from eas_coelemu_app.models import Usuario

class AdminForm(ModelForm):
    class Meta:
        model = Usuario
        fields = (
            'nombres',
            'apellido_paterno',
            'apellido_materno', 
            'rut', 
            'celular', 
            'email', 
            'contrasena'
            )

# Generated by Django 4.0.4 on 2022-06-19 20:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eas_coelemu_app', '0007_cantidadconvenio_estado'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cantidadconvenio',
            old_name='cantidad_canvenios',
            new_name='cantidad_convenios',
        ),
    ]

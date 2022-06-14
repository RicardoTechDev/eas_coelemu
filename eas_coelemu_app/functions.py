#Función que permite separar el RUT del Digito verificador
def formRut(rut_sin_form):
    rut = ''
    dv = ''
    
    for indice in range(len(rut_sin_form)):
        if(rut_sin_form[indice]=="-"):
            dv = rut_sin_form[indice+1]
            break
        else:
            rut += rut_sin_form[indice]

    rut_form ={
        'rut' : rut,
        'dv' : dv
    }

    return rut_form
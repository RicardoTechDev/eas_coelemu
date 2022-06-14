from django.shortcuts import redirect


def loginRequired(function):

    def wrapper(request, *args):
        if 'usuario' not in request.session:
            return redirect('login')
        resp = function(request, *args)
        return resp
    
    return wrapper
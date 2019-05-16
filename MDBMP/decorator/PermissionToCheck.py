from MDBMP import models
from django.shortcuts import redirect


def permission_check(menu_id):
    menu_id = menu_id

    def _permission_check(func):
        def wrapper(request, *args, **kwargs):
            user_id = request.session['_auth_user_id']
            user_menu_obj = models.UserMenus.objects.filter(user_id=user_id, menu_id=menu_id)
            if user_menu_obj.exists():
                return func(request)
            else:
                return redirect('/no_permission/')
        return wrapper
    return _permission_check

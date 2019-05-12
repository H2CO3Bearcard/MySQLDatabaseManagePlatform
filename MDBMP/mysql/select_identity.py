from MDBMP import models


def admin_yes_or_no(request):
    user_id = request.session.get("_auth_user_id")
    usermenu_number = models.UserMenus.objects.filter(user_id=user_id).count()
    menus_number = models.Menus.objects.all().count()
    if usermenu_number == menus_number:
        return "管理员"
    else:
        return "普通用户"

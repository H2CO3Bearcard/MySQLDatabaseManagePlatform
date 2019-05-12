from MDBMP import models


def select_sidebar(request):
    user_id = request.session.get("_auth_user_id")
    menu_id_list = []
    usermenu_obj = models.UserMenus.objects.filter(user_id=user_id)
    for menu in usermenu_obj:
        menu_id_list.append(menu.menu_id)
    menus_obj = models.Menus.objects.filter(id__in=menu_id_list)
    menu_group_id_list = []
    for menu_grouop in menus_obj:
        menu_group_id_list.append(menu_grouop.menu_group_id)
    menu_grouop_obj = models.MenusGroup.objects.filter(id__in=menu_group_id_list)
    return menus_obj, menu_grouop_obj

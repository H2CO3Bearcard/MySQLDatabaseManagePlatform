from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import json
import django.db.utils
from MDBMP import models
from MDBMP.mysql.select_identity import admin_yes_or_no
from MDBMP.mysql.sidebar import select_sidebar
from MDBMP.server import link_server
from MDBMP.server.execute_server_cmd import get_cpu, get_mem, get_hostname
from MDBMP.mysql.json_date import JsonExtendEncoder
from MDBMP.mysql.mysql_conn import create_mysql_conn
# Create your views here.


def login(request):
    if request.method == "POST":
        user = request.POST.get("username")
        pwd = request.POST.get("password")
        auth_user = auth.authenticate(username=user, password=pwd)
        if auth_user:
            auth.login(request, auth_user)
            status = 1
            url = "/index/"
            return HttpResponse(json.dumps({
                'status': status,
                'url': url
            }))
        else:
            status = 0
            err_msg = "输入的用户名或者密码有误，请重新输入！"
            return HttpResponse(json.dumps({
                'status': status,
                "err_msg": err_msg
            }))
    return render(request, "login.html")


@login_required
def logout(request):
    auth.logout(request)
    return redirect('/login/')


@login_required
def index(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    user_number = User.objects.all().count()
    return render(
        request,
        "index.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity,
         "user_number": user_number})


@login_required
def server_manage(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    server_obj = models.Server.objects.all()
    return render(
        request,
        "server_manage.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity,
         "server_obj": server_obj})


@login_required
def add_server(request):
    ip = request.POST.get("ip")
    port = request.POST.get("port")
    user = request.POST.get("user")
    password = request.POST.get("password")
    result = models.Server.objects.filter(ip=ip)
    if result.exists():
        status = 3
        err_msg = "IP地址存在，如要添加，请删除原主机"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        ssh_conn = link_server.ssh_conn_host(ip, port, user, password)
        if ssh_conn == 1:
            status = 1
            err_msg = "连接失败，请检查IP、用户名、密码是否错误"
            return HttpResponse(json.dumps({"status": status, "err_msg":err_msg}))
        elif ssh_conn == 2:
            status = 2
            err_msg = "连接超时，请检查IP、用户名、密码是否错误"
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
        else:
            status = 0
            url = "/server_manage/"
            hostname = get_hostname(ssh_conn)
            cpu_number = get_cpu(ssh_conn)
            mem_total = get_mem(ssh_conn)
            ssh_conn.close()
            server_obj = models.Server(ip=ip,
                                       hostname=hostname,
                                       user=user,
                                       password=password,
                                       cpu_number=cpu_number,
                                       mem_total=mem_total,
                                       ssh_port=port)
            server_obj.save()
            return HttpResponse(json.dumps({"status": status, "url": url}))


@login_required
def db_manage(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "db_manage.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


@login_required
def get_db_group(request):
    db, cur = create_mysql_conn()
    sql = "select * from MDBMP_databasegroup"
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    print(data)
    db.close()
    return HttpResponse(data)


@login_required
def add_db_group(request):
    group_name = request.POST.get("group_name")
    use = request.POST.get("use")
    label = request.POST.get("label")
    result = models.DatabaseGroup.objects.filter(group_name=group_name)
    if result.exists():
        status = 0
        err_msg = "数据库组存在，请重新输入"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        status = 1
        url = '/db_manage/'
        sql = "insert into MDBMP_databasegroup(group_name,group_use,date,group_label,instance_number) values(%s,%s,now(),%s,0)"
        db, cur = create_mysql_conn()
        cur.execute(sql, [group_name, use, label])
        db.commit()
        db.close()
        return HttpResponse(json.dumps({"status": status, "url": url}))


@login_required
def delete_db_group(request):
    group_id = request.POST.get("group_id")
    db, cur = create_mysql_conn()
    sql = "select instance_number from MDBMP_databasegroup where id=%s"
    cur.execute(sql, group_id)
    data = cur.fetchall()
    instance_number = int(data[0]["instance_number"])
    if instance_number == 0:
        sql = "delete from MDBMP_databasegroup where id=%s"
        cur.execute(sql, group_id)
        db.commit()
        db.close()
        status = 1
        url = "/db_manage/"
        return HttpResponse(json.dumps({"status": status, "url": url}))
    else:
        db.close()
        status = 0
        err_msg = "数据库组中存在数据库实例，禁止删除"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))


@login_required
def get_db_instance(request):
    db, cur = create_mysql_conn()
    group_id = request.GET.get("group_id", None)
    print(group_id)
    if int(group_id) > 0:
        sql = "select a.group_name,b.* from MDBMP_databaseinstance b, MDBMP_databasegroup a where a.id = b.group_id and  a.id=%s"
        cur.execute(sql, group_id)
    else:
        sql = "select a.group_name,b.* from MDBMP_databaseinstance b, MDBMP_databasegroup a where a.id = b.group_id"
        cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    print(data)
    db.close()
    return HttpResponse(data)


@login_required
def delete_server(request):
    server_id = request.POST.get("server_id")
    print(server_id)
    server_obj = models.Server.objects.get(id=server_id)
    server_obj.delete()
    status = 1
    return HttpResponse(json.dumps({"status": status}))


@login_required
def user_manage(request):
    user_obj_all = User.objects.all()
    usermenu_obj_all = models.UserMenus.objects.all()
    menus_obj_all = models.Menus.objects.all()
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "user_manage.html",
        {"user_obj_all": user_obj_all,
         "menus_obj_all": menus_obj_all,
         "usermenu_obj_all": usermenu_obj_all,
         "menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


@login_required
def create_user(request):
    if request.method == 'POST':
        get_user = request.POST.get("user")
        get_email = request.POST.get("email")
        get_password = request.POST.get("password")
        try:
            user = User.objects.create_user(username=get_user, password=get_password, email=get_email)
        except django.db.utils.IntegrityError:
            user = False
        if not user:
            status = 0
            err_msg = "用户已存在，请重新输入"
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
        else:
            status = 1
            user_id = user.id
            new_menu_id = models.UserMenus(menu_id=1, user_id=user_id)
            new_menu_id.save()
            return HttpResponse(json.dumps({"status": status}))


@login_required
def edit_user(request):
    if request.method == 'POST':
        get_password = request.POST.get("password")
        get_id = request.POST.get("id")
        user_obj = User.objects.get(id=get_id)
        if request.user == user_obj:
            user_obj.set_password(get_password)
            user_obj.save()
            logout(request)
            status = 0
            err_msg = "当前用户密码已更改，请重新登录"
            url = "/user_manage/"
            return HttpResponse(json.dumps({
                "status": status,
                "err_msg": err_msg,
                "url": url
            }))
        else:
            user_obj.set_password(get_password)
            user_obj.save()
            status = 1
            return HttpResponse(json.dumps({
                "status": status
            }))


@login_required
def delete_user(request):
    if request.method == "POST":
        get_user = request.POST.get("user")
        user = User.objects.get(username=get_user)
        user_id = user.id
        if request.user == user:
            status = 0
            err_mag = "当前登录用户和删除用户相同，不允许删除"
            return HttpResponse(json.dumps({"status": status, "err_msg": err_mag}))
        else:
            menu_obj = models.UserMenus.objects.filter(user_id=user_id)
            status = 1
            user.delete()
            menu_obj.delete()
            return HttpResponse(json.dumps({"status": status}))


@login_required
def permission(request):
    user_obj_all = User.objects.all()
    usermenu_obj_all = models.UserMenus.objects.all()
    menus_obj_all = models.Menus.objects.all()
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "permission.html",
        {"user_obj_all": user_obj_all,
         "menus_obj_all": menus_obj_all,
         "usermenu_obj_all": usermenu_obj_all,
         "menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


@login_required
def get_permission(request):
    user_id = request.POST.get("user_id")
    menu_id_list = []
    menu_obj = models.UserMenus.objects.filter(user_id=user_id)
    for i in menu_obj:
        menu_id_list.append(i.menu_id)
    return HttpResponse(json.dumps({
        "menu_id_list": menu_id_list
    }))


@login_required
def edit_permission(request):
    menu_id_list = request.POST.getlist("menus_list")
    user_id = request.POST.get("user_id")
    user_obj = User.objects.get(id=user_id)
    menu_obj = models.UserMenus.objects.filter(user_id=user_id).exclude(menu_id__in=[1])
    menu_obj.delete()
    for menu_id in menu_id_list:
        menu_create_obj = models.UserMenus(user_id=user_id, menu_id=menu_id)
        menu_create_obj.save()
    if request.user == user_obj:
        status = 0
        err_msg = "当前用户权限已修改，请重新登录"
        url = "/login/"
        logout(request)
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg, "url": url}))
    else:
        status = 1
        err_msg = "用户权限修改成功"
        url = "/permission/"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg, "url": url}))


@login_required
def db_monitor(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "db_monitor.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


def err(request):
    return render(request, '404.html')

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
from MDBMP.mysql.mysql_package import get_mysql_package
from MDBMP.mysql.install_mysql import send_package, install_mysql_ins
from MDBMP.mysql.start_or_stop_mysql import start_mysql, stop_mysql
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
            err_msg = "连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
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
def delete_server(request):
    server_id = request.POST.get("server_id")
    db_ins_obj = models.DatabaseInstance.objects.filter(server_id=server_id)
    if db_ins_obj.exists():
        status = 0
        err_msg = "当前主机还存在数据库实例，不可删除"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        server_obj = models.Server.objects.get(id=server_id)
        server_obj.delete()
        status = 1
        return HttpResponse(json.dumps({"status": status}))



@login_required
def db_manage(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    server_obj = models.Server.objects.values('id', 'ip', 'hostname')
    file = get_mysql_package()
    identity = admin_yes_or_no(request)
    return render(
        request,
        "db_manage.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         'server_obj': server_obj,
         "identity": identity,
         "file": file
         })


@login_required
def get_db_group(request):
    db, cur = create_mysql_conn()
    sql = "select * from MDBMP_databasegroup"
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
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
    if int(group_id) > 0:
        sql = "select a.group_name,b.* " \
              "from MDBMP_databaseinstance b, MDBMP_databasegroup a " \
              "where a.id = b.group_id and  a.id=%s"
        cur.execute(sql, group_id)
    else:
        sql = "select a.group_name,b.* " \
              "from MDBMP_databaseinstance b, MDBMP_databasegroup a " \
              "where a.id = b.group_id"
        cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    db.close()
    return HttpResponse(data)


@login_required
def install_mysql(request):
    group_id = request.POST.get("group_id")
    server_id = request.POST.get("server_id")
    pack_name = request.POST.get("pack_name")
    backup_name = request.POST.get("backup_name")
    ins_name = request.POST.get("ins_name")
    port = request.POST.get("port")
    alias = request.POST.get("alias")
    username = request.POST.get("username")
    password = request.POST.get("password")
    high_availability = request.POST.get("high_availability")
    path = request.POST.get("path")
    if backup_name:
        pass
    else:
        server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port').get(id=server_id)
        ip = server_obj['ip']
        server_user = server_obj['user']
        server_pwd = server_obj['password']
        ssh_port = server_obj['ssh_port']
        result = models.DatabaseInstance.objects.filter(server_id=server_id, port=port)
        if result.exists():
            status = 6
            err_msg = "当前主机({})上存在{}端口,请检查是否填写错误".format(ip, port)
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
        else:
            ssh_conn = link_server.ssh_conn_host(ip, ssh_port, server_user, server_pwd)
            if ssh_conn == 1:
                status = 1
                err_msg = "SSH连接失败，请检查IP、用户名、密码是否错误"
                return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
            elif ssh_conn == 2:
                status = 2
                err_msg = "SSH连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
                return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
            else:
                sftp_conn = link_server.sftp_conn_host(ip, ssh_port, server_user, server_pwd)
                if sftp_conn == 1:
                    status = 3
                    err_msg = "SFTP连接失败，请检查IP、用户名、密码是否错误"
                    return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                elif sftp_conn == 2:
                    status = 4
                    err_msg = "SFTP连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
                    return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                else:
                    send_package(sftp_conn, ssh_conn, pack_name)
                    sftp_conn.close()
                    stdout, mysql_version = install_mysql_ins(ssh_conn, pack_name, port, path, username, password, 'mysql', 'mysql', ip)
                    if stdout == 0:
                        status = 7
                        err_msg = mysql_version
                        sftp_conn.close()
                        ssh_conn.close()
                        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                    else:
                        status = 5
                        url = '/db_manage/'
                        dbins_obj = models.DatabaseInstance(
                            server_id=server_id,
                            mysql_version=mysql_version,
                            group_id=group_id,
                            instance_id=ins_name,
                            instance_alias=alias,
                            username=username,
                            password=password,
                            mysql_path=path,
                            port=port,
                            high_availability=high_availability)
                        dbins_obj.save()
                        db_group_obj = models.DatabaseGroup.objects.get(id=group_id)
                        db_group_obj.instance_number = db_group_obj.instance_number + 1
                        db_group_obj.save()
                        sftp_conn.close()
                        ssh_conn.close()
                        return HttpResponse(json.dumps({"status": status, "url": url}))


@login_required
def start_mysql_ins(request):
    server_id = request.POST.get("server_id")
    port = request.POST.get("port")
    server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port').get(id=server_id)
    ip = server_obj['ip']
    server_user = server_obj['user']
    server_pwd = server_obj['password']
    ssh_port = server_obj['ssh_port']
    ssh_conn = link_server.ssh_conn_host(ip, ssh_port, server_user, server_pwd)
    if ssh_conn == 1:
        status = 1
        err_msg = "SSH连接失败，请检查IP、用户名、密码是否错误"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    elif ssh_conn == 2:
        status = 2
        err_msg = "SSH连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        result = start_mysql(ssh_conn, port)
        if result == 1:
            status = 3
            err_msg = "当前实例正在运行，无需重复启动"
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
        elif result == 0:
            status = 4
            url = '/db_manage/'
            db_ins_obj = models.DatabaseInstance.objects.get(server_id=server_id, port=port)
            db_ins_obj.status = '运行'
            db_ins_obj.save()
            return HttpResponse(json.dumps({"status": status, "url": url}))
        else:
            status = 5
            err_msg = result
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))


@login_required
def stop_mysql_ins(request):
    server_id = request.POST.get("server_id")
    port = request.POST.get("port")
    server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port').get(id=server_id)
    ip = server_obj['ip']
    server_user = server_obj['user']
    server_pwd = server_obj['password']
    ssh_port = server_obj['ssh_port']
    ssh_conn = link_server.ssh_conn_host(ip, ssh_port, server_user, server_pwd)
    if ssh_conn == 1:
        status = 1
        err_msg = "SSH连接失败，请检查IP、用户名、密码是否错误"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    elif ssh_conn == 2:
        status = 2
        err_msg = "SSH连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        result = stop_mysql(ssh_conn, port)
        if result == 1:
            status = 3
            err_msg = "当前实例已停止运行，无需重复停止"
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
        elif result == 0:
            status = 4
            url = '/db_manage/'
            db_ins_obj = models.DatabaseInstance.objects.get(server_id=server_id, port=port)
            db_ins_obj.status = '停止'
            db_ins_obj.save()
            return HttpResponse(json.dumps({"status": status, "url": url}))
        else:
            status = 5
            err_msg = result
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))


@login_required
def get_rman_path(request):
    server_id = request.POST.get("server_id")
    server_obj = models.Server.objects.values('rman_path', 'ip').filter(id=server_id)
    rman_path = server_obj[0]['rman_path']
    ip = server_obj[0]['ip']
    if rman_path:
        return HttpResponse(json.dumps({"status": 1}))
    else:
        return HttpResponse(json.dumps({"status": 0, "ip": ip}))


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

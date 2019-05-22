from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import HttpResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import json
import time
import pymysql
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
from MDBMP.mysql import backup
from MDBMP.decorator.PermissionToCheck import permission_check
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
            response = HttpResponse(json.dumps({
                'status': status,
                'url': url
            }))
            return response
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
    rep = redirect('/login/')
    auth.logout(request)
    return rep


@login_required
@permission_check(1)
def index(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    user_number = User.objects.all().count()
    server_number = User.objects.all().count()
    failed_db = models.DatabaseInstance.objects.filter(status='停止').count()
    online_db = models.DatabaseInstance.objects.filter(status='运行').count()
    return render(
        request,
        "index.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity,
         "user_number": user_number,
         "server_number": server_number,
         "failed_db": failed_db,
         "online_db": online_db})


@login_required
@permission_check(3)
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
@permission_check(3)
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
@permission_check(3)
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
@permission_check(4)
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
@permission_check(4)
def get_db_group(request):
    db, cur = create_mysql_conn()
    sql = "select * from MDBMP_databasegroup"
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    db.close()
    return HttpResponse(data)


@login_required
@permission_check(4)
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
@permission_check(4)
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
@permission_check(4)
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
@permission_check(4)
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
    ins_number = models.DatabaseInstance.objects.filter(group_id=group_id).count()
    if ins_number == 0:
        role = '主实例'
    else:
        role = '从实例'
    server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port', 'rman_path').get(id=server_id)
    ip = server_obj['ip']
    server_user = server_obj['user']
    server_pwd = server_obj['password']
    ssh_port = server_obj['ssh_port']
    rman_path = server_obj['rman_path']
    print(rman_path)
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
                if backup_name:
                    if not rman_path:
                        return HttpResponse(json.dumps({"status": 8, "ip": ip}))
                    ins_obj = models.DatabaseInstance.objects.values('password', 'mysql_version').get(group_id=group_id, role='主实例')
                    password = ins_obj['password']
                    pack_name = 'mysql-{}-linux-glibc2.12-x86_64.tar.gz'.format(ins_obj['mysql_version'])
                    send_package(sftp_conn, ssh_conn, pack_name)
                    sftp_conn.close()
                    print(password)
                    print(pack_name)
                    print(backup_name)
                    backup_ins_id = backup_name.split("_")[1]
                    print(backup_ins_id)
                    backup_ins_obj = models.DatabaseInstance.objects.values('server_id', 'port', 'mysql_path').get(instance_id=backup_ins_id)
                    backup_ins_server_id = backup_ins_obj['server_id']
                    backup_ins_port = backup_ins_obj['port']
                    backup_ins_mysql_path = backup_ins_obj['mysql_path']
                    backup_path = backup_ins_mysql_path + '/mysql/backup/' + str(backup_ins_port) + '/' + backup_name
                    print(backup_path)
                    rman_tmp = rman_path + '/rman/tmp'
                    print(rman_path)
                    print(rman_tmp)
                    print(type(server_id))
                    print(type(backup_ins_server_id))
                    if int(server_id) == int(backup_ins_server_id):
                        print(1)
                        cp_backup_cmd = '''cp -r {} {}'''.format(backup_path, rman_tmp)
                        ssh_conn.exec_command(cp_backup_cmd)
                        backup.end_of_judgment_execution(ssh_conn, cp_backup_cmd)
                    else:
                        print(2)
                        backup_server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port',
                                                                          'rman_path').get(id=backup_ins_server_id)
                        backup_server_ip = backup_server_obj['ip']
                        backup_server_user = backup_server_obj['user']
                        backup_server_pwd = backup_server_obj['password']
                        backup_server_port = backup_server_obj['ssh_port']
                        backup_server_rman_path = backup_server_obj['rman_path']
                        backup_ssh_conn = link_server.ssh_conn_host(backup_server_ip, backup_server_port, backup_server_user, backup_server_pwd)
                        if backup_ssh_conn == 1:
                            status = 1
                            err_msg = "备份服务器SSH连接失败，请检查IP、用户名、密码是否错误"
                            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                        elif backup_ssh_conn == 2:
                            status = 2
                            err_msg = "备份服务器SSH连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
                            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                        else:
                            path_cmd = 'export PATH={}/rman/bin:$PATH;'.format(backup_server_rman_path)
                            scp_backup_cmd = '''{}scp.sh {} {} {} {} {} '''.format(path_cmd, backup_path, server_user, ip, rman_tmp, server_pwd)
                            print(scp_backup_cmd)
                            backup_ssh_conn.exec_command(scp_backup_cmd)
                            backup.end_of_judgment_execution(ssh_conn, scp_backup_cmd)
                            backup_ssh_conn.close()
                            stdout, mysql_version = install_mysql_ins(ssh_conn, pack_name, port, path, username,
                                                                      password, ip, high_availability, role)
                            if stdout == 0:
                                status = 7
                                err_msg = mysql_version
                                ssh_conn.close()
                                return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                            else:
                                if path[-1] == "/":
                                    mysql_path = path + "mysql"
                                    mysql_conf = path + "mysql/etc/" + str(port) + '/my.cnf'
                                else:
                                    mysql_path = path + "/mysql"
                                    mysql_conf = path + "/mysql/etc/" + str(port) + '/my.cnf'
                                backup_obj = models.DatabaseBackup.objects.values('backup_name','gtid').get(backup_folder_name=backup_name)
                                backup_folder_name = backup_obj['backup_name']
                                gtid = backup_obj['gtid']
                                backup.recover(ssh_conn, rman_path, mysql_conf, backup_name, backup_folder_name, ins_name)
                                ssh_conn.exec_command('''chown -R mysql:mysql {}'''.format(mysql_path))
                                start_mysql_cmd = '''systemctl start mysqld_{}'''.format(str(port))
                                ssh_conn.exec_command(start_mysql_cmd)
                                backup.end_of_judgment_execution(ssh_conn, start_mysql_cmd)
                                path_cmd = 'export PATH={}/base/{}/bin/:$PATH;'.format(mysql_path, mysql_version)
                                print(path_cmd)
                                sql = '''{}mysql -uroot -p{} -h{} -P{} -e "reset master"'''.format(path_cmd,password, ip, port)
                                print(sql)
                                k,c,v = ssh_conn.exec_command(sql)
                                vv = v.read().decode(encoding='UTF-8')
                                print('1'+vv)
                                sql = '''{}mysql -uroot -p{} -h{} -P{} -e "reset slave"'''.format(path_cmd,password, ip, port)
                                print(sql)
                                k,c,v =ssh_conn.exec_command(sql)
                                vv = v.read().decode(encoding='UTF-8')
                                print('2'+vv)
                                sql = '''{}mysql -uroot -p{} -h{} -P{} -e "set global gtid_purged='{}'"'''.format(path_cmd,password, ip, port, gtid)
                                print(sql)
                                k,c,v =ssh_conn.exec_command(sql)
                                vv = v.read().decode(encoding='UTF-8')
                                print('3'+vv)
                                sql = '''{}mysql -uroot -p{} -h{} -P{} -e "CHANGE MASTER TO MASTER_HOST='{}',MASTER_USER='root',MASTER_PASSWORD='{}',MASTER_PORT={},MASTER_AUTO_POSITION=1,MASTER_CONNECT_RETRY=1"'''.format(path_cmd, password, ip, port, backup_server_ip, password, backup_ins_port)
                                print(sql)
                                k,c,v =ssh_conn.exec_command(sql)
                                vv = v.read().decode(encoding='UTF-8')
                                print('4'+vv)
                                sql = '''{}mysql -uroot -p{} -h{} -P{} -e "start slave"'''.format(path_cmd,password, ip, port)
                                print(sql)
                                k,c,v =ssh_conn.exec_command(sql)
                                vv = v.read().decode(encoding='UTF-8')
                                print('5'+vv)
                                status = 5
                                url = '/db_manage/'
                                db_ins_obj = models.DatabaseInstance(
                                    server_id=server_id,
                                    mysql_version=mysql_version,
                                    group_id=group_id,
                                    instance_id=ins_name,
                                    instance_alias=alias,
                                    username='root',
                                    password=password,
                                    mysql_path=path,
                                    port=port,
                                    high_availability=high_availability,
                                    status='运行',
                                    role=role)
                                db_ins_obj.save()
                                db_group_obj = models.DatabaseGroup.objects.get(id=group_id)
                                db_group_obj.instance_number = db_group_obj.instance_number + 1
                                db_group_obj.save()
                                ssh_conn.close()
                                return HttpResponse(json.dumps({"status": status, "url": url}))
                else:
                    send_package(sftp_conn, ssh_conn, pack_name)
                    sftp_conn.close()
                    stdout, mysql_version = install_mysql_ins(ssh_conn, pack_name, port, path, username, password, ip, high_availability, role)
                    if stdout == 0:
                        status = 7
                        err_msg = mysql_version
                        sftp_conn.close()
                        ssh_conn.close()
                        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
                    else:
                        status = 5
                        url = '/db_manage/'
                        db_ins_obj = models.DatabaseInstance(
                            server_id=server_id,
                            mysql_version=mysql_version,
                            group_id=group_id,
                            instance_id=ins_name,
                            instance_alias=alias,
                            username=username,
                            password=password,
                            mysql_path=path,
                            port=port,
                            high_availability=high_availability,
                            status='运行',
                            role=role)
                        db_ins_obj.save()
                        db_group_obj = models.DatabaseGroup.objects.get(id=group_id)
                        db_group_obj.instance_number = db_group_obj.instance_number + 1
                        db_group_obj.save()
                        ssh_conn.close()
                        return HttpResponse(json.dumps({"status": status, "url": url}))


@login_required
@permission_check(4)
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
@permission_check(4)
def stop_mysql_ins(request):
    server_id = request.POST.get("server_id")
    port = request.POST.get("port")
    server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port').get(id=server_id)
    db_obj = models.DatabaseInstance.objects.values('role', 'group_id').get(server_id=server_id, port=port)
    online_number = models.DatabaseInstance.objects.filter(group_id=db_obj['group_id'], status='运行').count()
    if db_obj['role'] == '主实例' and online_number > 1:
        status = 6
        err_msg = "主实例必须成为当前组的最后一个实例"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
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
@permission_check(4)
def write_off_ins(request):
    server_id = request.POST.get('server_id')
    port = request.POST.get("port")
    ins_obj = models.DatabaseInstance.objects.values('group_id', 'instance_id').get(server_id=server_id, port=port)
    group_id = ins_obj['group_id']
    instance_id = ins_obj['instance_id']
    db_group_obj = models.DatabaseGroup.objects.get(id=group_id)
    db_group_obj.instance_number = db_group_obj.instance_number - 1
    db_group_obj.save()
    models.DatabaseInstance.objects.get(server_id=server_id, port=port).delete()
    models.DatabaseBackup.objects.filter(ins_id=instance_id).delete()
    return HttpResponse(json.dumps({"status": 1}))


@login_required
@permission_check(4)
def delete_ins(request):
    server_id = request.POST.get('server_id')
    port = request.POST.get("port")
    print(server_id)
    print(port)
    server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port').get(id=server_id)
    ip = server_obj['ip']
    server_user = server_obj['user']
    server_pwd = server_obj['password']
    ssh_port = server_obj['ssh_port']
    ins_obj = models.DatabaseInstance.objects.values('group_id', 'instance_id', 'mysql_path').get(server_id=server_id, port=port)
    group_id = ins_obj['group_id']
    instance_id = ins_obj['instance_id']
    mysql_path = ins_obj['mysql_path']
    conf_dir = mysql_path + '/mysql/etc/'+str(port)
    mysql_data = mysql_path + '/mysql/data/'+str(port)
    mysql_binlog_dir = mysql_path + "/mysql/log/binlog/" + str(port)
    mysql_redolog = mysql_path + "/mysql/log/redolog/" + str(port)
    mysql_relaylog_dir = mysql_path + "/mysql/log/relaylog/" + str(port)
    backup_dir = mysql_path + "/mysql/backup/" + str(port)
    tmp_dir = mysql_path + "/mysql/tmp/" + str(port)
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
        ssh_conn.exec_command('''systemctl stop mysqld_{}'''.format(str(port)))
        time.sleep(5)
        ssh_conn.exec_command('''rm -rf {}'''.format(conf_dir))
        ssh_conn.exec_command('''rm -rf {}'''.format(mysql_data))
        ssh_conn.exec_command('''rm -rf {}'''.format(mysql_binlog_dir))
        ssh_conn.exec_command('''rm -rf {}'''.format(mysql_redolog))
        ssh_conn.exec_command('''rm -rf {}'''.format(mysql_relaylog_dir))
        ssh_conn.exec_command('''rm -rf {}'''.format(backup_dir))
        ssh_conn.exec_command('''rm -rf {}'''.format(tmp_dir))
        ssh_conn.exec_command('''rm -rf /etc/systemd/system/mysqld_{}.service'''.format(str(port)))
        db_group_obj = models.DatabaseGroup.objects.get(id=group_id)
        db_group_obj.instance_number = db_group_obj.instance_number - 1
        db_group_obj.save()
        models.DatabaseInstance.objects.get(server_id=server_id, port=port).delete()
        models.DatabaseBackup.objects.filter(ins_id=instance_id).delete()
        ssh_conn.close()
        return HttpResponse(json.dumps({"status": 3}))


@login_required
@permission_check(4)
def get_rman_path(request):
    server_id = request.POST.get("server_id")
    server_obj = models.Server.objects.values('rman_path', 'ip').filter(id=server_id)
    rman_path = server_obj[0]['rman_path']
    ip = server_obj[0]['ip']
    if rman_path:
        return HttpResponse(json.dumps({"status": 1, "ip": ip}))
    else:
        return HttpResponse(json.dumps({"status": 0, "ip": ip}))


@login_required
@permission_check(4)
def install_rman(request):
    server_ip = request.POST.get("server_ip")
    rman_path = request.POST.get("rman_path")
    server_obj = models.Server.objects.values('ip', 'user', 'password', 'ssh_port').get(ip=server_ip)
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
            backup.upload_rman_tools(sftp_conn)
            backup.mkdir_rman(ssh_conn, rman_path)
            backup.unpack_package(ssh_conn, rman_path)
            server_obj = models.Server.objects.get(ip=server_ip)
            server_obj.rman_path = rman_path
            server_obj.save()
            ssh_conn.close()
            return HttpResponse(json.dumps({'status': 5}))


@login_required
@permission_check(4)
def ins_backup(request):
    server_ip = request.POST.get("server_ip")
    ins_id = request.POST.get("ins_id")
    server_id = request.POST.get("server_id")
    ins_obj = models.DatabaseInstance.objects.values('port', 'username', 'password', 'mysql_path').get(instance_id=ins_id)
    server_obj = models.Server.objects.values('rman_path', 'user', 'password', 'ssh_port').get(id=server_id)
    mysql_port = ins_obj['port']
    mysql_username = ins_obj['username']
    mysql_password = ins_obj['password']
    mysql_path = ins_obj['mysql_path']
    rman_path = server_obj['rman_path']
    ssh_user = server_obj['user']
    ssh_password = server_obj['password']
    ssh_port = server_obj['ssh_port']
    ssh_conn = link_server.ssh_conn_host(server_ip, ssh_port, ssh_user, ssh_password)
    if ssh_conn == 1:
        status = 1
        err_msg = "SSH连接失败，请检查IP、用户名、密码是否错误"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    elif ssh_conn == 2:
        status = 2
        err_msg = "SSH连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        result = backup.db_backup(ssh_conn, ins_id, mysql_port, mysql_username, mysql_password, mysql_path, rman_path)
        if result['backup'] == 1:
            status = 4
            backup_date = result['backup_date']
            backup_folder_name = result['backup_folder_name']
            backup_name = result['backup_name']
            gtid = result['gtid']
            backup_file_size = result['backup_file_size']
            backup_status = '成功'
            backup_obj = models.DatabaseBackup(ins_id=ins_id,
                                               backup_date=backup_date,
                                               backup_folder_name=backup_folder_name,
                                               backup_name=backup_name,
                                               gtid=gtid,
                                               backup_file_size=backup_file_size,
                                               backup_status=backup_status)
            backup_obj.save()
            return HttpResponse(json.dumps({"status": status}))
        elif result['backup'] == 0:
            backup_date = result['backup_date']
            backup_folder_name = result['backup_folder_name']
            backup_name = result['backup_name']
            backup_status = '失败'
            status = 3
            err_msg = "备份失败，请查看{}下{}/mysql/backup/{}/{}/{}.log。".format(mysql_path,
                                                                        server_ip,
                                                                        str(mysql_port),
                                                                        backup_folder_name,
                                                                        backup_name)
            backup_obj = models.DatabaseBackup(ins_id=ins_id,
                                               backup_date=backup_date,
                                               backup_folder_name=backup_folder_name,
                                               backup_name=backup_name,
                                               backup_status=backup_status)
            backup_obj.save()
            return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))


def get_backup(request):
    group_id = request.POST.get("group_id")
    print(type(group_id))
    sql = "select backup_folder_name from MDBMP_databaseinstance a,MDBMP_databasebackup b " \
          "where a.instance_id=b.ins_id and a.group_id=%s"
    db, cur = create_mysql_conn()
    cur.execute(sql, group_id)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    db.close()
    return HttpResponse(data)


@login_required
@permission_check(5)
def backup_manage(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "backup_manage.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


@login_required
@permission_check(5)
def get_backup_set(request):
    db, cur = create_mysql_conn()
    sql = "select a.id,backup_date,instance_alias, instance_id, '手工触发' AS 'backup_strategy'," \
          "'XtraBackup' AS 'backup_tool',backup_file_size, '全备' AS 'backup_type'," \
          "backup_status, backup_folder_name from MDBMP_databasebackup a,MDBMP_databaseinstance b " \
          "where a.ins_id=b.instance_id;"
    cur.execute(sql)
    data = cur.fetchall()
    db.close()
    data = json.dumps(data, cls=JsonExtendEncoder)
    return HttpResponse(data)


@login_required
@permission_check(5)
def delete_backup_set(request):
    backup_id = request.POST.get("backup_id")
    print(backup_id)
    backup_obj = models.DatabaseBackup.objects.values('ins_id', 'backup_folder_name').get(id=backup_id)
    ins_id = backup_obj['ins_id']
    backup_folder_name = backup_obj['backup_folder_name']
    print(ins_id)
    print(backup_folder_name)
    ins_obj = models.DatabaseInstance.objects.values('server_id', 'mysql_path', 'port').get(instance_id=ins_id)
    server_id = ins_obj['server_id']
    mysql_path = ins_obj['mysql_path']
    mysql_port = ins_obj['port']
    server_obj = models.Server.objects.values('ip', 'ssh_port', 'user', 'password').get(id=server_id)
    ssh_ip = server_obj['ip']
    ssh_port = server_obj['ssh_port']
    ssh_user = server_obj['user']
    ssh_pwd = server_obj['password']
    ssh_conn = link_server.ssh_conn_host(ssh_ip, ssh_port, ssh_user, ssh_pwd)
    if ssh_conn == 1:
        status = 1
        err_msg = "SSH连接失败，请检查IP、用户名、密码是否错误"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    elif ssh_conn == 2:
        status = 2
        err_msg = "SSH连接超时，请检查IP、用户名、密码是否错误,网络是否畅通"
        return HttpResponse(json.dumps({"status": status, "err_msg": err_msg}))
    else:
        backup_path = '''{}/mysql/backup/{}/{}'''.format(mysql_path, str(mysql_port), backup_folder_name)
        ssh_conn.exec_command('''rm -rf {}'''.format(backup_path))
        models.DatabaseBackup.objects.get(id=backup_id).delete()
        ssh_conn.close()
        return HttpResponse(json.dumps({"status": 3}))


@login_required
@permission_check(8)
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
@permission_check(8)
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
@permission_check(8)
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
@permission_check(8)
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
@permission_check(9)
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
@permission_check(9)
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
@permission_check(9)
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
@permission_check(2)
def db_monitor(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "db_monitor.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


def get_monitor_data(request):
    data = request.body.decode(encoding='UTF-8')
    data = json.loads(data)
    ip = data['ip']
    data_time = data['date_time']
    free_used = data['free_used']
    cpu_load = data['cpu_load']
    run_time = data['run_time']
    monitor_obj = models.MonitorData(ip=ip, date=data_time, free_used=free_used, cpu_load=cpu_load, run_time=run_time)
    monitor_obj.save()
    return HttpResponse("OK")


def get_mysql_monitor_data(request):
    data = request.body.decode(encoding='UTF-8')
    data = json.loads(data)
    read = data['read']
    ip = data['ip']
    Slow_queries = data['Slow_queries']
    Threads_created = data['Threads_created']
    TPS = data['TPS']
    ibp_read_requests = data['ibp_read_requests']
    port = data['port']
    Connections = data['Connections']
    date_time = data['date_time']
    write = data['write']
    Questions = data['Questions']
    ibp_not_read_requests = data['ibp_not_read_requests']
    QPS = data['QPS']
    monitor_obj = models.MySQLMonitorData(ip=ip, port=port, date=date_time, read=read, write=write, QPS=QPS, TPS=TPS,
                                          ibp_read_requests=ibp_read_requests, ibp_not_read_requests=ibp_not_read_requests,
                                          Slow_queries=Slow_queries, Threads_created=Threads_created, Connections=Connections,
                                          Questions=Questions)
    monitor_obj.save()
    return HttpResponse("OK")


@login_required
@permission_check(1)
def index_get_monitor(request):
    db, cur = create_mysql_conn()
    sql = "select date,cpu_load,free_used from MDBMP_monitordata order by id desc limit 10"
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    db.close()
    return HttpResponse(data)


@login_required
@permission_check(2)
def db_monitor_get(request):
    db, cur = create_mysql_conn()
    sql = "select QPS,TPS,date from MDBMP_mysqlmonitordata order by id desc limit 10"
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    db.close()
    return HttpResponse(data)


@login_required
@permission_check(2)
def db_monitor2_get(request):
    db, cur = create_mysql_conn()
    sql = "select `read`,`write`,Slow_queries,Threads_created,ibp_not_read_requests," \
          "ibp_read_requests,Connections,Questions from MDBMP_mysqlmonitordata order by id desc limit 1"
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    db.close()
    return HttpResponse(data)


@login_required
def no_permission(request):
    return render(request, 'nopermission.html')


@login_required
@permission_check(6)
def sql_submit(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    ins_obj = models.DatabaseInstance.objects.values('id', 'instance_id', 'instance_alias').filter(role='主实例')
    return render(
        request,
        "sql_submit.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity,
         "ins_obj": ins_obj})


@login_required
@permission_check(6)
def get_db(request):
    ins_id = request.POST.get("ins_id")
    mysql_user = request.POST.get("mysql_user")
    mysql_pwd = request.POST.get("mysql_pwd")
    ins_obj = models.DatabaseInstance.objects.values('server_id', 'port').get(id=ins_id)
    server_id = ins_obj['server_id']
    mysql_port = ins_obj['port']
    server_obj = models.Server.objects.values('ip').get(id=server_id)
    mysql_ip = server_obj['ip']
    try:
        db = pymysql.connect(host=mysql_ip, user=mysql_user, passwd=mysql_pwd, port=mysql_port)
    except pymysql.err.OperationalError as error:
        return HttpResponse(json.dumps({'status': 0, "error": repr(error)}))
    else:
        cur = db.cursor(cursor=pymysql.cursors.DictCursor)
        cur.execute("show databases")
        data = cur.fetchall()
        databases = json.dumps(data, cls=JsonExtendEncoder)
        return HttpResponse(json.dumps({'status': 1, "databases": databases}))


@login_required
@permission_check(6)
def submit_audit(request):
    ins_id = request.POST.get("ins_id")
    mysql_user = request.POST.get("mysql_user")
    mysql_pwd = request.POST.get("mysql_pwd")
    mysql_db = request.POST.get("mysql_db")
    sql = request.POST.get("sql")
    apply_user = request.POST.get("apply_user")
    apply_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sql_audit_obj = models.SQLAudit(ins_id=ins_id,
                                    mysql_user=mysql_user,
                                    mysql_password=mysql_pwd,
                                    mysql_db=mysql_db,
                                    sql_statement=sql,
                                    audit_status='未审核',
                                    online_status='未上线',
                                    apply_user=apply_user,
                                    apply_date=apply_date)
    sql_audit_obj.save()
    return HttpResponse(json.dumps({"status": 1}))


@login_required
@permission_check(6)
def get_to_audit(request):
    apply_user = request.GET.get("apply_user")
    db, cur = create_mysql_conn()
    sql = "select a.id,instance_alias,mysql_db,sql_statement,audit_status,apply_date,mysql_user " \
          "from MDBMP_sqlaudit a,MDBMP_databaseinstance b " \
          "where a.ins_id=b.id and a.audit_status='未审核' and a.apply_user=%s"
    cur.execute(sql, apply_user)
    data = cur.fetchall()
    db.close()
    return HttpResponse(json.dumps(data, cls=JsonExtendEncoder))


@login_required
@permission_check(6)
def get_to_pass_audit(request):
    apply_user = request.GET.get("apply_user")
    db, cur = create_mysql_conn()
    sql = "select a.id,instance_alias,mysql_db,sql_statement,audit_status,audit_user" \
          ",apply_date,mysql_user,online_status,online_date,audit_date " \
          "from MDBMP_sqlaudit a,MDBMP_databaseinstance b " \
          "where a.ins_id=b.id and a.audit_status='已通过' and a.apply_user=%s"
    cur.execute(sql, apply_user)
    data = cur.fetchall()
    db.close()
    return HttpResponse(json.dumps(data, cls=JsonExtendEncoder))


@login_required
@permission_check(6)
def get_to_not_pass_audit(request):
    apply_user = request.GET.get("apply_user")
    db, cur = create_mysql_conn()
    sql = "select a.id,instance_alias,mysql_db,sql_statement,audit_status,audit_date,audit_user" \
          ",apply_date,mysql_user,reasons_for_failure " \
          "from MDBMP_sqlaudit a,MDBMP_databaseinstance b " \
          "where a.ins_id=b.id and a.audit_status='未通过' and a.apply_user=%s"
    cur.execute(sql, apply_user)
    data = cur.fetchall()
    db.close()
    return HttpResponse(json.dumps(data, cls=JsonExtendEncoder))


@login_required
@permission_check(7)
def checked(request):
    audit_user = request.GET.get("audit_user")
    db, cur = create_mysql_conn()
    sql = "select instance_alias,mysql_db,sql_statement,audit_status,audit_date," \
          "apply_date,mysql_user,reasons_for_failure,online_status,apply_user,online_date " \
          "from MDBMP_sqlaudit a,MDBMP_databaseinstance b " \
          "where a.ins_id=b.id and a.audit_user=%s"
    cur.execute(sql, audit_user)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    print(data)
    return HttpResponse(data)


@login_required
@permission_check(7)
def pass_audit(request):
    id = request.POST.get("id")
    audit_user = request.POST.get("audit_user")
    audit_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sql_obj = models.SQLAudit.objects.get(id=id)
    sql_obj.audit_user = audit_user
    sql_obj.audit_date = audit_date
    sql_obj.audit_status = '已通过'
    sql_obj.save()
    return HttpResponse(json.dumps({"status": 0}))


@login_required
@permission_check(7)
def not_pass_audit(request):
    id = request.POST.get("id")
    reasons_for_failure = request.POST.get("reasons_for_failure")
    audit_user = request.POST.get("audit_user")
    audit_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sql_obj = models.SQLAudit.objects.get(id=id)
    sql_obj.audit_user = audit_user
    sql_obj.audit_date = audit_date
    sql_obj.audit_status = '未通过'
    sql_obj.reasons_for_failure = reasons_for_failure
    sql_obj.save()
    return HttpResponse(json.dumps({"status": 0}))


@login_required
@permission_check(7)
def nocheck(request):
    sql = "select a.id,instance_alias,mysql_db,sql_statement,audit_status,apply_date,apply_user,mysql_user " \
          "from MDBMP_sqlaudit a,MDBMP_databaseinstance b where a.ins_id=b.id and a.audit_status='未审核'"
    db, cur = create_mysql_conn()
    cur.execute(sql)
    data = cur.fetchall()
    data = json.dumps(data, cls=JsonExtendEncoder)
    return HttpResponse(data)


@login_required
@permission_check(6)
def online_sql(request):
    id = request.POST.get("id")
    print(id)
    sql = "select ip,port,mysql_user,mysql_password,mysql_db,sql_statement " \
          "from MDBMP_server a,MDBMP_databaseinstance b,MDBMP_sqlaudit c " \
          "where a.id=b.server_id and b.id=c.ins_id and c.id=%s"
    db, cur = create_mysql_conn()
    cur.execute(sql, id)
    data = cur.fetchall()
    db.close()
    mysql_ip = data[0]['ip']
    mysql_port = data[0]['port']
    mysql_user = data[0]['mysql_user']
    mysql_password = data[0]['mysql_password']
    mysql_db = data[0]['mysql_db']
    sql_statement = data[0]['sql_statement']
    try:
        db = pymysql.connect(host=mysql_ip, user=mysql_user, passwd=mysql_password, port=mysql_port, db=mysql_db)
        cur = db.cursor()
        cur.execute(sql_statement)
        db.commit()
        cur.close()
    except (pymysql.err.OperationalError, pymysql.err.ProgrammingError, pymysql.err.InternalError) as error:
        return HttpResponse(json.dumps({'status': 1, "error": repr(error)}))
    else:
        online_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql_obj = models.SQLAudit.objects.get(id=id)
        sql_obj.online_status = '已上线'
        sql_obj.online_date = online_date
        sql_obj.save()
        return HttpResponse(json.dumps({"status": 0}))


@login_required
@permission_check(7)
def sql_audit(request):
    menus_obj, menu_grouop_obj = select_sidebar(request)
    identity = admin_yes_or_no(request)
    return render(
        request,
        "sql_audit.html",
        {"menus_obj": menus_obj,
         "menu_grouop_obj": menu_grouop_obj,
         "identity": identity})


@login_required
def err(request):
    return render(request, '404.html')

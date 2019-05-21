import random
import time
import traceback


def send_file(sftp_conn, ssh_conn, file_name):
    # 获取创建的连接对象
    ssh_conn = ssh_conn
    file_name = file_name

    # 判断目录下是否已存在文件
    stdin, stdout, stderr = ssh_conn.exec_command("ls /tmp/{}".format(file_name))
    result = stdout.read().decode(encoding="UTF-8")
    if result:
        print("文件存在，传输结束")
        return 1
    else:
        # 不存在就传输文件
        sftp_conn = sftp_conn
        local_path = "./MDBMP/mysql_related/config/" + file_name
        server_path = "/tmp/" + file_name
        sftp_conn.put(local_path, server_path)
        return 0


# 上传安装包
def send_package(sftp_conn, ssh_conn, package_name):
    # 获取创建的连接对象
    ssh_conn = ssh_conn
    mysql_package = package_name
    # 获取安装包版本
    version = float(mysql_package.partition("-")[2].partition("-")[0].rpartition(".")[0])
    # 判断目录下是否已存在安装包
    stdin, stdout, stderr = ssh_conn.exec_command("ls /tmp/{}".format(mysql_package))
    result = stdout.read().decode(encoding="UTF-8")
    if result:
        print("文件存在，传输结束")
        if version == 5.7:
            send_file(sftp_conn, ssh_conn, "my_5_7.cnf")
            send_file(sftp_conn, ssh_conn, "mysql_5_7.systemd")
        else:
            send_file(sftp_conn, ssh_conn, "my_5_6.cnf")
            send_file(sftp_conn, ssh_conn, "mysql_5_6.systemd")
        return 1
    else:
        # 不存在就传输安装包
        sftp_conn = sftp_conn
        local_path = "./MDBMP/mysql_related/mysql_package/" + mysql_package
        server_path = "/tmp/" + mysql_package
        sftp_conn.put(local_path, server_path)
        if version == 5.7:
            send_file(sftp_conn, ssh_conn, "my_5_7.cnf")
            send_file(sftp_conn, ssh_conn, "mysql_5_7.systemd")
        else:
            send_file(sftp_conn, ssh_conn, "my_5_6.cnf")
            send_file(sftp_conn, ssh_conn, "mysql_5_6.systemd")
        return 0


class ModifyMysqlCnf(object):
    def __init__(self, ssh_conn, cnf_dir):
        self.ssh_conn = ssh_conn
        self.cnf_dir = cnf_dir

    def modify_cnf(self, var_option, var_values):
        var_option = var_option
        var_values = var_values
        cnf_dir = self.cnf_dir + "/my.cnf"
        stdin, stdout, stderr = self.ssh_conn.exec_command("egrep -iw {} {}".format(var_option, cnf_dir))
        potion = stdout.read().decode(encoding='UTF-8').strip("\n")
        time.sleep(0.2)
        stdin,stdout,stderr = self.ssh_conn.exec_command('''sed -i 's;{};{} = {};' {}'''.format(potion, var_option, var_values, cnf_dir))
        time.sleep(0.3)

    def modify_systemd(self, privilege_user, privilege_group, mysql_pid, mysql_base, mysql_cnf, mysql_socket, mysql_port):
        privilege_user = privilege_user
        privilege_group = privilege_group
        mysql_pid = mysql_pid
        mysql_base = mysql_base
        mysql_cnf = mysql_cnf
        mysql_socket = mysql_socket
        mysql_port = mysql_port
        systemd_file = '/etc/systemd/system/mysqld_{}.service'.format(mysql_port)

        self.ssh_conn.exec_command('''mv {} {}'''.format("/tmp/mysql_5_7.systemd", systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's/{{.RunUser}}/{}/g' {}'''.format(privilege_user, systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's/{{.RunGroup}}/{}/g' {}'''.format(privilege_group, systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's;{{.PidPath}};{};g' {}'''.format(mysql_pid, systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's;{{.BaseDir}};{};g' {}'''.format(mysql_base, systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's;{{.Mycnf}};{};g' {}'''.format(mysql_cnf+"/my.cnf", systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's;{{.SocketPath}};{};g' {}'''.format(mysql_socket, systemd_file))
        time.sleep(0.3)
        self.ssh_conn.exec_command('''sed -i 's;{{.Port}};{};g' {}'''.format(mysql_port, systemd_file))

    def empowerment(self, dir_name, pri_user, pri_group):
        dir_name = dir_name
        pri_user = pri_user
        pri_group = pri_group
        stdin,stdout,stderr = self.ssh_conn.exec_command('''chown -R {}:{} {}'''.format(pri_user, pri_group, dir_name))

    def make_dir(self, dir_name, pri_user, pri_group):
        dir_name = dir_name
        pri_user = pri_user
        pri_group = pri_group
        stdin,stdout,stderr = self.ssh_conn.exec_command('''mkdir -p {}'''.format(dir_name))
        stdin,stdout,stderr = self.ssh_conn.exec_command('''chown -R {}:{} {}'''.format(pri_user, pri_group, dir_name))
        time.sleep(1)

    def create_user(self, pri_user, pri_group):
        pri_user = pri_user
        pri_group = pri_group
        self.ssh_conn.exec_command('''groupadd {}'''.format(pri_group))
        stdin, stdout, stderr = self.ssh_conn.exec_command('''id {}'''.format(pri_user))
        out = stdout.read().decode(encoding='UTF-8')
        if out:
            print("用户存在")
        else:
            self.ssh_conn.exec_command('useradd --no-log-init --no-create-home -g {} {}'.format(pri_group, pri_user))

    def judge_dir(self, dir_name):
        dir_name = dir_name
        stdin, stdout, stderr = self.ssh_conn.exec_command('''ls {}'''.format(dir_name))
        out = stdout.read().decode(encoding='UTF-8')
        if out:
            return 0
        else:
            return 1

    def move_file(self, old_location, new_location):
        old_location = old_location
        new_location = new_location
        stdin,stdout,stderr = self.ssh_conn.exec_command('''mv {} {}'''.format(old_location, new_location))

    def unpack_package(self, mysql_package, unpack_dir):
        mysql_package = '/tmp/' + mysql_package
        unpack_dir = unpack_dir
        cmd = '''tar -x -f {} -C {} --strip-components=1'''.format(mysql_package, unpack_dir)
        cmd2 = '''ps -ef |grep "{}" | grep -v grep'''.format(cmd)
        self.ssh_conn.exec_command(cmd)
        stdin, stdout, stderr = self.ssh_conn.exec_command(cmd2)
        out = stdout.read().decode(encoding='UTF-8')
        while True:
            if out:
                time.sleep(5)
                stdin, stdout, stderr = self.ssh_conn.exec_command(cmd2)
                out = stdout.read().decode(encoding='UTF-8')
            else:
                return 0

    def run_mysql(self, mysql_base, mysql_user, mysql_password, pri_user, mysql_port, mysql_socket):
        mysql_base = mysql_base
        user = mysql_user
        password = mysql_password
        pri_user = pri_user
        mysql_cnf = self.cnf_dir + "/my.cnf"
        mysql_port = mysql_port
        mysql_socket = mysql_socket
        cmd = "{}/bin/mysqld --defaults-file={} --initialize-insecure --user={}".format(mysql_base, mysql_cnf, pri_user)
        cmd2 = '''ps -ef |grep "{}" |grep -v grep'''.format(cmd)
        self.ssh_conn.exec_command(cmd)
        stdin, stdout, stderr = self.ssh_conn.exec_command(cmd2)
        out = stdout.read().decode(encoding='UTF-8')
        while True:
            if out:
                time.sleep(5)
                stdin, stdout, stderr = self.ssh_conn.exec_command(cmd2)
                out = stdout.read().decode(encoding='UTF-8')
            else:
                self.ssh_conn.exec_command("systemctl daemon-reload")
                time.sleep(5)
                cmd3 = "systemctl start mysqld_{}.service".format(mysql_port)
                cmd4 = '''ps -ef |grep "{}" |grep -v grep '''.format(cmd3)
                self.ssh_conn.exec_command(cmd3)
                stdin, stdout, stderr = self.ssh_conn.exec_command(cmd4)
                out = stdout.read().decode(encoding='UTF-8')
                while True:
                    if out:
                        time.sleep(5)
                        stdin, stdout, stderr = self.ssh_conn.exec_command(cmd4)
                        out = stdout.read().decode(encoding='UTF-8')
                    else:
                        cmd7 = '''grant all on *.* to root@'%' identified by '{}' with grant option;'''.format(password)
                        cmd5 = '''flush privileges;set password for root@localhost = \\"{}\\";{};flush privileges'''.format(password, cmd7)
                        cmd6 = '''{}/bin/mysql -u{} -S {} -e "{}"'''.format(mysql_base, user, mysql_socket, cmd5)
                        self.ssh_conn.exec_command(cmd6)
                        return 0


def install_mysql_ins(ssh_conn, mysql_package, mysql_port, mysql_dir, mysql_user, mysql_password, hostname, ha_mode, role):
    try:
        ssh_conn = ssh_conn
        hostname = hostname
        ha_mode = ha_mode
        role = role
        mysql_package = mysql_package
        mysql_version = mysql_package.partition("-")[2].partition("-")[0]
        mysql_port = mysql_port
        mysql_server_id = random.randint(1, 4294967295)
        mysql_dir = mysql_dir
        if mysql_dir[-1] == "/":
            mysql_dir = mysql_dir + "mysql"
        else:
            mysql_dir = mysql_dir + "/mysql"
        mysql_base = mysql_dir + "/base/" + mysql_version
        mysql_data = mysql_dir + "/data/" + str(mysql_port)
        mysql_log = mysql_dir + "/log"
        mysql_binlog_dir = mysql_log + "/binlog/" + str(mysql_port)
        mysql_binlog = mysql_binlog_dir + "/mysql_bin"
        mysql_redolog = mysql_log + "/redolog/" + str(mysql_port)
        mysql_relaylog_dir = mysql_log + "/relaylog/" + str(mysql_port)
        mysql_relaylog = mysql_relaylog_dir + "/mysql-relay"
        mysql_err = mysql_data + "/mysql-error.log"
        mysql_slow = mysql_data + "/mysql-slow.log"
        mysql_tmp = mysql_dir + "/tmp/" + str(mysql_port)
        mysql_backup = mysql_dir + "/backup/" + str(mysql_port)
        mysql_cnf = mysql_dir + "/etc/" + str(mysql_port)
        mysql_socket = mysql_data + "/mysqld.sock"
        mysql_pid = mysql_data + "/mysqld.pid"
        install_mysql_lock_file = mysql_dir + "/base/" + mysql_version + '/INSTALL_MYSQL_LOCK'
        privilege_user = 'mysql'
        privilege_group = 'mysql'
        mysql_user = mysql_user
        mysql_password = mysql_password
        modifly = ModifyMysqlCnf(ssh_conn, mysql_cnf)
        modifly.create_user('mysql', 'mysql')
        if modifly.judge_dir(mysql_dir) == 1:
            modifly.make_dir(mysql_dir, privilege_user, privilege_group)
        if modifly.judge_dir(install_mysql_lock_file) == 1:
            modifly.make_dir(mysql_base, privilege_user, privilege_group)
            ssh_conn.exec_command("touch {}".format(install_mysql_lock_file))
            modifly.make_dir(mysql_base, privilege_user, privilege_group)
            modifly.unpack_package(mysql_package, mysql_base)
        else:
            print("base目录存在")
        list = [mysql_data, mysql_log, mysql_binlog_dir, mysql_redolog, mysql_relaylog_dir, mysql_tmp, mysql_backup, mysql_cnf]
        for i in list:
            modifly.make_dir(i, privilege_user, privilege_group)
        modifly.empowerment(mysql_dir, privilege_user, privilege_group)
        modifly.move_file("/tmp/my_5_7.cnf", "{}/my.cnf".format(mysql_cnf))
        modifly.empowerment("{}/my.cnf".format(mysql_cnf), privilege_user, privilege_group)
        modifly.modify_cnf("port", mysql_port)
        modifly.modify_cnf("server_id", mysql_server_id)
        modifly.modify_cnf("basedir", mysql_base)
        modifly.modify_cnf("datadir", mysql_data)
        modifly.modify_cnf("log_bin", mysql_binlog)
        modifly.modify_cnf("tmpdir", mysql_tmp)
        modifly.modify_cnf("relay_log", mysql_relaylog)
        modifly.modify_cnf("innodb_log_group_home_dir", mysql_redolog)
        modifly.modify_cnf("log_error", mysql_err)
        modifly.modify_cnf("slow_query_log_file", mysql_slow)
        modifly.modify_cnf("socket", mysql_socket)
        modifly.modify_cnf("pid_file", mysql_pid)
        modifly.modify_cnf("report_host", hostname)
        if ha_mode == '主从复制-异步模式':
            modifly.modify_cnf("rpl_semi_sync_slave_enabled", 0)
        else:
            modifly.modify_cnf("rpl_semi_sync_slave_enabled", 1)
        modifly.modify_systemd(privilege_user, privilege_group, mysql_pid, mysql_base, mysql_cnf, mysql_socket, mysql_port)
        if role == '主实例':
            modifly.run_mysql(mysql_base, mysql_user, mysql_password, privilege_user, mysql_port, mysql_socket)
    except Exception as err:
        error = traceback.format_exc(err)
        return 0, error
    else:
        return 1, mysql_version


if __name__ == '__main__':
    pass

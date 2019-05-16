import time


def upload_rman_tools(sftp_conn):
    sftp_conn = sftp_conn
    local_path = "./MDBMP/mysql_related/rman/rman-backup-tools.tar.gz"
    server_path = "/tmp/rman-backup-tools.tar.gz"
    sftp_conn.put(local_path, server_path)
    return 0


def mkdir_rman(ssh_conn, rman_path):
    ssh_conn = ssh_conn
    rman_path = rman_path
    if rman_path[-1] == "/":
        rman_path = rman_path + "rman"
    else:
        rman_path = rman_path + "/rman/tmp"
    ssh_conn.exec_command('''mkdir -p {}'''.format(rman_path))
    time.sleep(1)
    return 0


def unpack_package(ssh_conn, rman_path):
    mysql_package = '/tmp/rman-backup-tools.tar.gz'
    if rman_path[-1] == "/":
        rman_path = rman_path + "rman"
    else:
        rman_path = rman_path + "/rman/"
    rman_path = rman_path
    cmd = '''tar -x -f {} -C {} '''.format(mysql_package, rman_path)
    cmd2 = '''ps -ef |grep "{}" | grep -v grep'''.format(cmd)
    ssh_conn.exec_command(cmd)
    stdin, stdout, stderr = ssh_conn.exec_command(cmd2)
    out = stdout.read().decode(encoding='UTF-8')
    while True:
        if out:
            time.sleep(5)
            stdin, stdout, stderr = ssh_conn.exec_command(cmd2)
            out = stdout.read().decode(encoding='UTF-8')
        else:
            return 0


if __name__ == '__main__':
    from MDBMP.server.link_server import ssh_conn_host, sftp_conn_host

    date = time.localtime()

    backup_file_date = time.strftime("%Y_%m_%d_%H_%M_%S", date)
    backup_date = time.strftime("%Y-%m-%d %H:%M:%S", date)
    ssh_conn = ssh_conn_host('192.168.1.4', 22, 'root', '123456')
    sftp_conn = sftp_conn_host('192.168.1.4', 22, 'root', '123456')
    upload_rman_tools(sftp_conn)
    mkdir_rman(ssh_conn, '/data')
    print(ssh_conn)
    print(sftp_conn)
    ssh_conn.close()
    sftp_conn.close()


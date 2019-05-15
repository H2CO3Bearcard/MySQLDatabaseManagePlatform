import time
from MDBMP.server.link_server import ssh_conn_host, sftp_conn_host
date = time.localtime()

backup_file_date = time.strftime("%Y_%m_%d_%H_%M_%S", date)
backup_date = time.strftime("%Y-%m-%d %H:%M:%S", date)


def upload_rman_tools(sftp_conn):
    sftp_conn = sftp_conn
    local_path = "./MDBMP/mysql_related/rman/rman-backup-tools.tar.gz"
    server_path = "/tmp/rman-backup-tools.tar.gz"
    sftp_conn.put(local_path, server_path)
    return 0


def mkdir_rman(ssh_conn, rman_path):
    ssh_conn = ssh_conn
    rman_path = rman_path
    ssh_conn.exec_command('''mkdir -p {}'''.format(rman_path))
    time.sleep(1)


if __name__ == '__main__':
    ssh_conn = ssh_conn_host('192.168.1.4', 22, 'root', '123456')
    sftp_conn = sftp_conn_host('192.168.1.4', 22, 'root', '123456')
    upload_rman_tools(sftp_conn)
    mkdir_rman(ssh_conn, '/data')
    print(ssh_conn)
    print(sftp_conn)
    ssh_conn.close()
    sftp_conn.close()


from MDBMP.server.link_server import ssh_conn_host
import time


def start_mysql(ssh_conn, port):
    ssh_conn = ssh_conn
    port = port
    stdin, stdout, stderr = ssh_conn.exec_command(
        '''netstat -nltp|grep 'LISTEN' |grep 'mysqld' | grep {}'''.format(port))
    sout = stdout.read().decode(encoding="UTF-8")
    if sout:
        print(sout)
        return 1
    else:
        stdin, stdout, stderr = ssh_conn.exec_command(
            '''systemctl start mysqld_{}'''.format(port))
        serr = stderr.read().decode(encoding="UTF-8")
        if serr:
            return serr
        else:
            return 0


def stop_mysql(ssh_conn, port):
    ssh_conn = ssh_conn
    port = port
    stdin, stdout, stderr = ssh_conn.exec_command(
        '''netstat -nltp|grep 'LISTEN' |grep 'mysqld' | grep {}'''.format(port))
    sout = stdout.read().decode(encoding="UTF-8")
    if sout:
        print(sout)
        stdin1, stdout1, stderr1 = ssh_conn.exec_command(
            '''systemctl stop mysqld_{}'''.format(port))
        time.sleep(1)
        stdin, stdout, stderr = ssh_conn.exec_command(
            '''netstat -nltp|grep 'LISTEN' |grep 'mysqld' | grep {}'''.format(port))
        sout = stdout.read().decode(encoding="UTF-8")
        if sout:
            serr1 = stderr1.read().decode(encoding="UTF-8")
            return serr1
        else:
            return 0
    else:
        return 1


if __name__ == '__main__':
    ssh_conn = ssh_conn_host('192.168.1.3', 22, 'root', '123456')
    print(ssh_conn)
    result = start_mysql(ssh_conn, 3306)
    # result = stop_mysql(ssh_conn, 3306)
    print(result)

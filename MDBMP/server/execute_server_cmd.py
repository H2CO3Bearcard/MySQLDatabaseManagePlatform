from MDBMP.server.link_server import ssh_conn_host


def get_hostname(ssh_conn):
    ssh_conn = ssh_conn
    stdin, stdout, stderr = ssh_conn.exec_command("hostname")
    hostname = stdout.read().decode(encoding='UTF-8').strip()
    return hostname


def get_cpu(ssh_conn):
    ssh_conn = ssh_conn
    stdin, stdout, stderr = ssh_conn.exec_command('''lscpu | grep -e "^CPU(s):" | awk '{print $2}' ''')
    cpu_number = stdout.read().decode(encoding='UTF-8').strip()
    return cpu_number


def get_mem(ssh_conn):
    ssh_conn = ssh_conn
    stdin, stdout, stderr = ssh_conn.exec_command('''free -h | grep 'Mem:' | awk '{print $2}' ''')
    mem_total = stdout.read().decode(encoding='UTF-8').strip()
    return mem_total


if __name__ == '__main__':
    ssh_conn = ssh_conn_host('192.168.1.3', 22, 'root', '123456')
    hostname = get_hostname(ssh_conn)
    print(hostname)
    cpunumber = get_cpu(ssh_conn)
    print(cpunumber)
    mem_total = get_mem(ssh_conn)
    print(mem_total)
    ssh_conn.close()
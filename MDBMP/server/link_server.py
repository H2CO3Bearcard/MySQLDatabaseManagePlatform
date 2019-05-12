import paramiko
import socket


# 创建ssh，并返回连接对象
def ssh_conn_host(hostname, port, username, password):
    # 连接服务器
    try:
        # 创建ssh连接对象
        ssh = paramiko.SSHClient()
        # 设置允许连接不在know_host文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=hostname, port=port, username=username, password=password, timeout=30)
        # 捕获认证失败的异常，并返回错误代码
    except paramiko.ssh_exception.AuthenticationException:
        return 1
    except socket.timeout:
        return 2
    else:
        return ssh


# 创建sftp，并返回连接对象
def sftp_conn_host(hostname, port, username, password):
    try:
        # 创建连接sftp连接对象
        t = paramiko.Transport((hostname, port))
        t.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(t)
        # 捕获认证失败的异常，并返回错误代码
    except paramiko.ssh_exception.AuthenticationException:
        return 1
    except paramiko.ssh_exception.SSHException:
        return 2
    else:
        return sftp


import time


def upload_rman_tools(sftp_conn):
    sftp_conn = sftp_conn
    local_path = "./MDBMP/mysql_related/rman/rman-backup-tools.tar.gz"
    server_path = "/tmp/rman-backup-tools.tar.gz"
    sftp_conn.put(local_path, server_path)
    sftp_conn.close()
    return 0


def mkdir_rman(ssh_conn, rman_path):
    ssh_conn = ssh_conn
    rman_path = rman_path
    if rman_path[-1] == "/":
        rman_path = rman_path + "rman/tmp"
        rman_log_path = rman_path + "rman/log"
    else:
        rman_path = rman_path + "/rman/tmp"
        rman_log_path = rman_path + "/rman/log"
    ssh_conn.exec_command('''mkdir -p {} {}'''.format(rman_path,rman_log_path))
    time.sleep(1)
    ssh_conn.close()
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
            ssh_conn.close()
            return 0


def db_backup(ssh_conn, ins_id, port, mysql_user, mysql_pwd, mysql_path, rman_path):
    ssh_conn = ssh_conn
    ins_id = ins_id
    port = port
    mysql_user = mysql_user
    mysql_pwd = mysql_pwd
    mysql_path = mysql_path
    rman_path = rman_path
    date = time.localtime()
    backup_file_date = time.strftime("%Y_%m_%d_%H_%M_%S", date)
    backup_date = time.strftime("%Y-%m-%d %H:%M:%S", date)
    backup_file_name = 'manual_'+ins_id+'_'+backup_file_date
    rman_tmp = rman_path+'/rman/tmp'
    ins_backup_path = mysql_path+'/mysql/backup/3306'
    path_cmd = '''export PATH={}/rman/bin/:$PATH;'''.format(rman_path)
    mysql_cnf = mysql_path+'/mysql/etc/'+str(port)+'/my.cnf'
    mysql_socket = mysql_path+'/mysql/data/'+str(port)+'/mysqld.sock'
    backup_log = backup_file_date+'.log'
    mkdir_cmd1 = '''mktemp -d -p {} tmp.rman.XXXXXXXXXX'''.format(rman_tmp)
    stdin, stdout, stderr = ssh_conn.exec_command(mkdir_cmd1)
    backup_path = stdout.read().decode(encoding='UTF-8').strip()
    time.sleep(0.5)
    mkdir_cmd2 = '''mktemp -d -p {} rman.work.XXXXXXXXXX'''.format(backup_path)
    stdin, stdout, stderr = ssh_conn.exec_command(mkdir_cmd2)
    backup_work_path = stdout.read().decode(encoding='UTF-8').strip()
    backup_cmd = '''{} xtrabackup --defaults-file={} --backup --target-dir={} \
    --parallel=4 --no-version-check --compress --compress-threads=2  --stream=xbstream --user={} \
    --password={} --socket={} > {}/{} 2>{}/{}'''.format(path_cmd, mysql_cnf, backup_work_path, mysql_user, mysql_pwd,
                                                        mysql_socket, backup_path, backup_file_date, backup_path,
                                                        backup_log)
    ssh_conn.exec_command(backup_cmd)
    ps_cmd = '''ps -ef | grep "xtrabackup --defaults-file={} --backup" |grep -v grep'''.format(mysql_cnf)
    stdin, stdout, stderr = ssh_conn.exec_command(ps_cmd)
    result = stdout.read().decode(encoding='UTF-8')
    while True:
        if result:
            time.sleep(3)
            stdin, stdout, stderr = ssh_conn.exec_command(ps_cmd)
            result = stdout.read().decode(encoding='UTF-8')
        else:
            break
    success_mark_cmd = '''grep "completed OK" {}/{}'''.format(backup_path, backup_log)
    stdin, stdout, stderr = ssh_conn.exec_command(success_mark_cmd)
    backup_status = stdout.read().decode(encoding='UTF-8').strip()
    ssh_conn.exec_command('''rm -rf {}'''.format(backup_work_path))
    ssh_conn.exec_command('''cp {} {}/my.cnf.bak'''.format(mysql_cnf, backup_path))
    if backup_status:
        gtid_cmd = '''grep "MySQL binlog position" {}/{} | \
        awk -F "[']" '{{print $6}}' |tee {}/gtid'''.format(backup_path, backup_log, backup_path)
        stdin, stdout, stderr = ssh_conn.exec_command(gtid_cmd)
        gtid = stdout.read().decode(encoding='UTF-8').strip()
        binlog_pos_cmd = '''grep "MySQL binlog position" {}/{} | \
        awk -F "[']" '{{print $2 " " $4}}' > {}/binlog_pos'''.format(backup_path, backup_log, backup_path)
        ssh_conn.exec_command(binlog_pos_cmd)
        ssh_conn.exec_command('''touch {}/_XtraBackup'''.format(backup_path))
        ssh_conn.exec_command('''mv {} {}/{}'''.format(backup_path, ins_backup_path, backup_file_name))
        stdin, stdout, stderr = ssh_conn.exec_command('''du -sh {}/{}'''.format(ins_backup_path, backup_file_name))
        c, v, k = ssh_conn.exec_command('''ps -ef "du -sh {}/{}" '''.format(ins_backup_path, backup_file_name))
        vv = v.read().decode(encoding='UTF-8')
        while True:
            if vv:
                time.sleep(2)
                c, v, k = ssh_conn.exec_command('''ps -ef "du -sh {}/{}" '''.format(ins_backup_path, backup_file_name))
                vv = v.read().decode(encoding='UTF-8')
            else:
                break
        backup_file_size = stdout.read().decode(encoding='UTF-8').strip().split()
        ssh_conn.close()
        return {"backup": 1,
                "backup_date": backup_date,
                "backup_folder_name": backup_file_name,
                "backup_name": backup_file_date,
                "gtid": gtid,
                "backup_file_size": backup_file_size[0]}
    else:
        ssh_conn.exec_command('''touch {}/_XtraBackup'''.format(backup_path))
        ssh_conn.exec_command('''mv {} {}/{}'''.format(backup_path, ins_backup_path, backup_file_name))
        ssh_conn.close()
        return {"backup": 0,
                "backup_date": backup_date,
                "backup_folder_name": backup_file_name,
                "backup_name": backup_file_date}


if __name__ == '__main__':
    from MDBMP.server.link_server import ssh_conn_host
    ssh_conn = ssh_conn_host('192.168.1.3', 22, 'root', '123456')
    result = db_backup(ssh_conn, 'mysql-123m12i32', 3306, 'root', '123456', '/data', '/data')
    print(result)
    ssh_conn.close()



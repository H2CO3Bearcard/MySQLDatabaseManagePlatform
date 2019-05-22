
import os
import json


def mysql_status():
    	status = os.popen(''' /data/mysql/base/5.7.21/bin/mysql -uroot -p123456 -S /data/mysql/data/3306/mysqld.sock -s -e "show global status" 2>/dev/null ''')
	result = {}
	for line in status.readlines():
		line = line.strip()
		if not len(line):
			break
		try:
			result[line.split()[0]] = line.split()[1]
		except IndexError:
			result[line.split()[0]] = ''
	return result

def mysql_monitor():
	mysql_status_dict = mysql_status()
	Questions=mysql_status_dict['Questions']
	Uptime=mysql_status_dict['Uptime']
	QPS = int(Questions)/int(Uptime)
	print(QPS)
	Com_commit = mysql_status_dict['Com_commit']
	Com_rollback = mysql_status_dict['Com_rollback']
	TPS = (int(Com_commit)+int(Com_rollback))/int(Uptime)
	print(TPS)
	ibp_read_requests = mysql_status_dict['Innodb_buffer_pool_read_requests']
	ibp_not_read_requests = int(mysql_status_dict['Innodb_buffer_pool_read_requests']) + int(mysql_status_dict['Innodb_buffer_pool_read_ahead']) + int(mysql_status_dict['Innodb_buffer_pool_reads'])
	read = int(mysql_status_dict['Com_select'])
	write = int(mysql_status_dict['Com_insert']) + int(mysql_status_dict['Com_update']) + int(mysql_status_dict['Com_delete'])
	Connections = int(mysql_status_dict['Connections'])
	Threads_created = int(mysql_status_dict['Threads_created'])
	Slow_queries = int(mysql_status_dict['Slow_queries'])
	Questions = int(mysql_status_dict['Questions'])
	result = {"QPS":QPS,"TPS":TPS,"ibp_read_requests":ibp_read_requests,"ibp_not_read_requests":ibp_not_read_requests,"read":read,"write":write,"Connections":Connections,"Threads_created":Threads_created,"Slow_queries":Slow_queries,"Questions":Questions}
	result = json.dumps(result)
	print(result)
mysql_monitor()

#!/usr/bin/env python
#-*- coding: utf-8 -*-
import urllib2
import json
import os
import time
import thread
ip = '10.211.55.11'
port = 3306
url = 'http://10.211.55.2:8000/get_monitor_data/'
url2 = 'http://10.211.55.2:8000/get_mysql_monitor_data/'
header_dict = {"Content-Type": "application/json"}

def run_time():
	return os.popen(''' w | head -n1 |awk -F [','] '{print $1}' ''').read().strip()

def cpu_load():
	return os.popen('''w | head -n1 |awk -F [','] '{print $6}' ''').read().strip()	

def free_used():
	return os.popen('''free -m | grep 'Mem' |awk '{print $3}' ''').read().strip()

def date_time():
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


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
        Com_commit = mysql_status_dict['Com_commit']
        Com_rollback = mysql_status_dict['Com_rollback']
        TPS = (int(Com_commit)+int(Com_rollback))/int(Uptime)
        ibp_read_requests = mysql_status_dict['Innodb_buffer_pool_read_requests']
        ibp_not_read_requests = int(mysql_status_dict['Innodb_buffer_pool_read_ahead']) + int(mysql_status_dict['Innodb_buffer_pool_reads'])
        read = int(mysql_status_dict['Com_select'])
        write = int(mysql_status_dict['Com_insert']) + int(mysql_status_dict['Com_update']) + int(mysql_status_dict['Com_delete'])
        Connections = int(mysql_status_dict['Connections'])
        Threads_created = int(mysql_status_dict['Threads_created'])
        Slow_queries = int(mysql_status_dict['Slow_queries'])
        Questions = int(mysql_status_dict['Questions'])
        result = {"ip":ip,"port":port,"date_time":date_time(),"QPS":QPS,"TPS":TPS,"ibp_read_requests":ibp_read_requests,"ibp_not_read_requests":ibp_not_read_requests,"read":read,"write":write,"Connections":Connections,"Threads_created":Threads_created,"Slow_queries":Slow_queries,"Questions":Questions}
        result = json.dumps(result)
	return result


def post_server_data(ip,url,header_dict):
	while True:
		data = {"ip":ip,"date_time":date_time(),"run_time":run_time(),"cpu_load":cpu_load(),"free_used":free_used()}
		data = json.dumps(data)
		try:
			req = urllib2.Request(url=url,data=data,headers=header_dict)
			res = urllib2.urlopen(req)
		except (urllib2.URLError,urllib2.HTTPError),err:
			pass
			time.sleep(5)
		else:
			time.sleep(5)

def post_db_data(url,header_dict):
	while True:
		data = mysql_monitor()
		try:
                        req = urllib2.Request(url=url,data=data,headers=header_dict)
                        res = urllib2.urlopen(req)
                except (urllib2.URLError,urllib2.HTTPError),err:
                        pass
                        time.sleep(5)
                else:
                        time.sleep(5)

thread.start_new_thread(post_server_data,(ip,url,header_dict))
thread.start_new_thread(post_db_data,(url2,header_dict))

while 1:
   pass







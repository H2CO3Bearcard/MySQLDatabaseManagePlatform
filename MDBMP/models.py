from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class MenusGroup(models.Model):
    id = models.AutoField(primary_key=True)
    group_name = models.CharField(null=False, unique=True, max_length=25)
    group_url = models.CharField(null=False, unique=False, max_length=50)
    group_icon = models.CharField(null=False, unique=False, max_length=50)


class Menus(models.Model):
    id = models.AutoField(primary_key=True)
    menu_name = models.CharField(null=False, unique=True, max_length=25)
    menu_url = models.CharField(null=False, unique=False, max_length=50)
    menu_group_id = models.IntegerField(null=False, unique=False)


class UserMenus(models.Model):
    id = models.AutoField(primary_key=True)
    menu_id = models.IntegerField(null=False, unique=False)
    user_id = models.IntegerField(null=False, unique=False)


class Server(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.CharField(max_length=50, unique=True, null=False)
    hostname = models.CharField(max_length=50, null=False, unique=False)
    user = models.CharField(max_length=100, null=False, unique=False)
    password = models.CharField(max_length=100, null=False)
    ssh_port = models.IntegerField(null=False, unique=False, default=22)
    cpu_number = models.IntegerField()
    mem_total = models.CharField(max_length=50)
    rman_path = models.CharField(null=True, max_length=50)


class DatabaseGroup(models.Model):
    id = models.AutoField(primary_key=True)
    group_name = models.CharField(null=False, unique=False, max_length=25)
    instance_number = models.IntegerField(null=False, unique=False, default=0)
    group_use = models.CharField(null=True, max_length=50)
    group_label = models.CharField(null=True, max_length=100)
    date = models.DateTimeField(null=False)


class DatabaseInstance(models.Model):
    id = models.AutoField(primary_key=True)
    server_id = models.IntegerField(null=False, unique=False)
    mysql_version = models.CharField(null=False, unique=False, max_length=50)
    group_id = models.IntegerField(null=False, unique=False)
    instance_id = models.CharField(null=False, unique=False, max_length=25)
    instance_alias = models.CharField(null=False, unique=False, max_length=50)
    username = models.CharField(null=False, unique=False, max_length=50)
    password = models.CharField(null=False, unique=False, max_length=50)
    mysql_path = models.CharField(null=False, unique=False, max_length=50)
    port = models.IntegerField(null=False)
    high_availability = models.CharField(null=False, max_length=25)
    role = models.CharField(null=False, max_length=25)
    status = models.CharField(null=False, max_length=25)


class DatabaseBackup(models.Model):
    id = models.AutoField(primary_key=True)
    backup_date = models.DateTimeField(null=False)
    ins_id = models.CharField(null=False, unique=False, max_length=25)
    backup_folder_name = models.CharField(null=False, unique=False, max_length=150)
    backup_name = models.CharField(null=False, unique=False, max_length=150)
    gtid = models.CharField(null=True, unique=False, max_length=150)
    backup_file_size = models.CharField(null=True, unique=False, max_length=150)
    backup_status = models.CharField(null=False, unique=False, max_length=150)


class SQLAudit(models.Model):
    id = models.AutoField(primary_key=True)
    ins_id = models.CharField(null=False, unique=False, max_length=25)
    mysql_user = models.CharField(null=False, unique=False, max_length=50)
    mysql_password = models.CharField(null=False, unique=False, max_length=50)
    mysql_db = models.CharField(null=False, unique=False, max_length=50)
    sql_statement = models.TextField(null=False, unique=False)
    audit_status = models.CharField(null=False, unique=False, max_length=50)
    online_status = models.CharField(null=False, unique=False, max_length=50)
    apply_user = models.CharField(null=False, unique=False, max_length=50)
    audit_user = models.CharField(null=True, unique=False, max_length=50)
    apply_date = models.DateTimeField(null=False)
    audit_date = models.DateTimeField(null=True)
    online_date = models.DateTimeField(null=True)
    reasons_for_failure = models.CharField(null=True, unique=False, max_length=500)

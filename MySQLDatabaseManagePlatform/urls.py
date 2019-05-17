"""MySQLDatabaseManagePlatform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from MDBMP import views


urlpatterns = [
    url(r'^login/', views.login),
    url(r'^logout/', views.logout),
    url(r'^index/', views.index),
    url(r'^user_manage/', views.user_manage),
    url(r'^create_user/', views.create_user),
    url(r'^delete_user/', views.delete_user),
    url(r'^edit_user/', views.edit_user),
    url(r'^permission/', views.permission),
    url(r'^server_manage/', views.server_manage),
    url(r'^add_server/', views.add_server),
    url(r'^delete_server/', views.delete_server),
    url(r'^db_manage/', views.db_manage),
    url(r'^get_db_group/', views.get_db_group),
    url(r'^add_db_group/', views.add_db_group),
    url(r'^delete_db_group/', views.delete_db_group),
    url(r'^get_db_instance/', views.get_db_instance),
    url(r'^install_mysql/', views.install_mysql),
    url(r'^start_mysql_ins/', views.start_mysql_ins),
    url(r'^stop_mysql_ins/', views.stop_mysql_ins),
    url(r'^write_off_ins/', views.write_off_ins),
    url(r'^delete_ins/', views.delete_ins),
    url(r'^get_rman_path/', views.get_rman_path),
    url(r'^install_rman/', views.install_rman),
    url(r'^ins_backup/', views.ins_backup),
    url(r'^backup_manage/', views.backup_manage),
    url(r'^get_backup/', views.get_backup),
    url(r'^delete_backup_set/', views.delete_backup_set),
    url(r'^get_backup_set/', views.get_backup_set),
    url(r'^get_permission/', views.get_permission),
    url(r'^edit_permission/', views.edit_permission),
    url(r'^db_monitor/', views.db_monitor),
    url(r'^no_permission/', views.no_permission),
    url(r'^.*/', views.err),
    url(r'^$', views.login),
]

# Generated by Django 2.2 on 2019-05-10 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MDBMP', '0003_server_ssh_port'),
    ]

    operations = [
        migrations.AlterField(
            model_name='server',
            name='mem_total',
            field=models.CharField(max_length=50),
        ),
    ]
# Generated by Django 2.2 on 2019-05-10 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Menus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('menu_name', models.CharField(max_length=25, unique=True)),
                ('menu_url', models.CharField(max_length=50)),
                ('menu_group_id', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MenusGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('group_name', models.CharField(max_length=25, unique=True)),
                ('group_url', models.CharField(max_length=50)),
                ('group_icon', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='UserMenus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('menu_id', models.IntegerField()),
                ('user_id', models.IntegerField()),
            ],
        ),
    ]
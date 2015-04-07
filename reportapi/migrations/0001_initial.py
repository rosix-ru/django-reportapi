# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations
from reportapi.models import upload_to
from reportapi.fields import JSONField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('restriction', models.IntegerField(verbose_name='restriction', null=True, editable=False, db_index=True)),
                ('code', models.CharField(db_index=True, max_length=32, verbose_name='process key', blank=True)),
                ('error', models.TextField(verbose_name='error message', blank=True)),
                ('start', models.DateTimeField(auto_now_add=True, verbose_name='start create')),
                ('end', models.DateTimeField(null=True, verbose_name='end create', blank=True)),
                ('report_file', models.FileField(upload_to=upload_to, max_length=512, verbose_name='report file', blank=True)),
                ('odf_file', models.FileField(upload_to=upload_to, max_length=512, verbose_name='report file in ODF', blank=True)),
                ('pdf_file', models.FileField(upload_to=upload_to, max_length=512, verbose_name='report file in PDF', blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title', blank=True)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('details', JSONField(null=True, verbose_name='details', blank=True)),
            ],
            options={
                'ordering': ['-start', '-end'],
                'get_latest_by': 'end',
                'verbose_name': 'generated report',
                'verbose_name_plural': 'generated reports',
            },
        ),
        migrations.CreateModel(
            name='Register',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('section', models.CharField(max_length=255, verbose_name='section')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('title', models.CharField(max_length=255, verbose_name='title without translation')),
                ('all_users', models.BooleanField(default=False, verbose_name='allow all users')),
                ('timeout', models.IntegerField(default=1000, verbose_name='max of timeout')),
                ('groups', models.ManyToManyField(to='auth.Group', verbose_name='allow list groups', blank=True)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='allow list users', blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'registered report',
                'verbose_name_plural': 'registered reports',
            },
        ),
        migrations.AddField(
            model_name='document',
            name='register',
            field=models.ForeignKey(verbose_name='registered report', to='reportapi.Register'),
        ),
        migrations.AddField(
            model_name='document',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='register',
            unique_together=set([('section', 'name')]),
        ),
    ]

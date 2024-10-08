# Generated by Django 5.1.1 on 2024-09-21 14:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_user_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpamReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reported_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='myapp.user')),
            ],
            options={
                'unique_together': {('phone_number', 'reported_by')},
            },
        ),
    ]

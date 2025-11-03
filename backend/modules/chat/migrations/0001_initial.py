# Generated migration for chat module

import django.db.models.deletion
import uuid
from django.db import migrations, models

import modules.core.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('investors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant')], max_length=20, verbose_name='Role')),
                ('content', models.TextField(verbose_name='Content')),
                ('timestamp', models.DateTimeField(default=modules.core.utils.get_local_datetime, verbose_name='Timestamp')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to='investors.investor', verbose_name='Investor')),
            ],
            options={
                'verbose_name': 'Chat Message',
                'verbose_name_plural': 'Chat Messages',
                'ordering': ['timestamp'],
            },
        ),
    ]

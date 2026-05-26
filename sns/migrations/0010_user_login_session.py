from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sns', '0009_add_performance_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLoginSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('last_seen_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('logout_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='login_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-login_at'],
            },
        ),
        migrations.AddIndex(
            model_name='userloginsession',
            index=models.Index(fields=['user', '-login_at'], name='sns_userlog_user_id_46f1fd_idx'),
        ),
        migrations.AddIndex(
            model_name='userloginsession',
            index=models.Index(fields=['logout_at', '-last_seen_at'], name='sns_userlog_logout__f93c71_idx'),
        ),
    ]

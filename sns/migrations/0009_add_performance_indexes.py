# Generated for Render performance tuning.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sns', '0008_alter_comment_created_at_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['user', '-created_at'], name='sns_post_user_id_2eb3c2_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['post', 'created_at'], name='sns_comment_post_id_9e78c1_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read', '-created_at'], name='sns_notific_recipie_2fd3f1_idx'),
        ),
    ]

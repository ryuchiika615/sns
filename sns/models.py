from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# 1. ガチャアイテムのマスターデータ
class GachaItem(models.Model):
    name = models.CharField(max_length=50)
    rarity = models.CharField(max_length=10,
                              choices=[('N', 'ノーマル'), ('R', 'レア'), ('SR', '激レア'), ('SSR', '超激レア')])
    image_url = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"[{self.rarity}] {self.name}"


# 2. プロフィール
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    theme_color = models.CharField(max_length=20, default='dark')
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False, blank=True)

    # 🔮 裏技：画像をデータベースにテキストとして直接保存する（絶対に消えない）
    icon = models.TextField(blank=True, null=True)

    target_date = models.DateField(null=True, blank=True)
    target_minutes = models.IntegerField(default=0)

    points = models.IntegerField(default=0)
    exchange_points = models.IntegerField(default=0)
    items = models.ManyToManyField(GachaItem, blank=True)
    current_title = models.CharField(max_length=100, default="新人エンジニア", blank=True)
    current_avatar = models.CharField(max_length=100, default="初期アバター", blank=True)

    def __str__(self):
        return self.user.username


# 3. 投稿モデル
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=140)

    # 🔮 裏技：投稿画像もデータベースに直接保存
    image = models.TextField(blank=True, null=True)

    subject = models.CharField(max_length=50, default="その他")
    study_minutes = models.IntegerField(default=0)

    # ⚡ 爆速化：db_index=True を追加し、数万件になっても並び替えを一瞬にする
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f'{self.user.username}: {self.content[:10]}'

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]


# 4. コメントモデル
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]


# 5. 通知モデル
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20,
                                         choices=[('like', 'いいね'), ('reply', 'リプライ'), ('follow', 'フォロー')])
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} ({self.notification_type})"

    class Meta:
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]


class UserLoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_sessions')
    login_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen_at = models.DateTimeField(auto_now=True, db_index=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} {self.login_at:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ['-login_at']
        indexes = [
            models.Index(fields=['user', '-login_at']),
            models.Index(fields=['logout_at', '-last_seen_at']),
        ]


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

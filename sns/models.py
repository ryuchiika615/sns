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


# 2. プロフィール（大幅拡張！）
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # --- 新規追加：プロフィールの充実 ---
    display_name = models.CharField(max_length=50, blank=True, null=True)  # 表示名
    bio = models.TextField(max_length=300, blank=True, null=True)  # 自己紹介(Bio)
    department = models.CharField(max_length=50, blank=True, null=True)  # 学科
    theme_color = models.CharField(max_length=20, default='dark')  # 背景色

    # --- 新規追加：フォロー機能 ---
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False, blank=True)

    # 既存の機能
    icon = models.ImageField(upload_to='icons/', default='icons/default.png', blank=True)
    points = models.IntegerField(default=0)
    items = models.ManyToManyField(GachaItem, blank=True)
    current_title = models.CharField(max_length=100, default="新人エンジニア", blank=True)
    current_avatar = models.CharField(max_length=100, default="初期アバター", blank=True)

    def __str__(self):
        return self.user.username


# 3. 投稿モデル（リプライ機能を追加！）
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=140)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    study_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    # --- 新規追加：どの投稿へのリプライかを記録するキー ---
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f'{self.user.username}: {self.content[:10]}'


# 4. コメントモデル（簡易コメント用として維持）
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


# 5. 通知モデル（★完全新規追加！）
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # 通知を受け取る人
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')  # 通知を送った人
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)  # 関連する投稿
    notification_type = models.CharField(max_length=20,
                                         choices=[('like', 'いいね'), ('reply', 'リプライ'), ('follow', 'フォロー')])
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} ({self.notification_type})"


# ユーザー作成時にプロフィールを自動作成する設定
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
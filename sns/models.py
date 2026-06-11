from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# 1. ガチャアイテムのマスターデータ
class GachaItem(models.Model):
    name = models.CharField('名前', max_length=50)
    rarity = models.CharField('レア度', max_length=10,
                              choices=[('N', 'ノーマル'), ('R', 'レア'), ('SR', '激レア'), ('SSR', '超激レア')])
    image_url = models.CharField('画像URL', max_length=200, blank=True)

    def __str__(self):
        return f"[{self.rarity}] {self.name}"

    class Meta:
        verbose_name = 'ガチャアイテム'
        verbose_name_plural = 'ガチャアイテム'


# 2. プロフィール
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    display_name = models.CharField('表示名', max_length=50, blank=True, null=True)
    bio = models.TextField('自己紹介', max_length=300, blank=True, null=True)
    department = models.CharField('部署', max_length=50, blank=True, null=True)
    theme_color = models.CharField('テーマカラー', max_length=20, default='dark')
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False, blank=True, verbose_name='フォロー')

    # 🔮 裏技：画像をデータベースにテキストとして直接保存する（絶対に消えない）
    icon = models.TextField('アイコン', blank=True, null=True)

    target_date = models.DateField('目標日', null=True, blank=True)
    target_minutes = models.IntegerField('目標時間(分)', default=0)

    points = models.IntegerField('ポイント', default=0)
    exchange_points = models.IntegerField('交換ポイント', default=0)
    items = models.ManyToManyField(GachaItem, blank=True, verbose_name='所持アイテム')
    current_title = models.CharField('現在の称号', max_length=100, default="新人エンジニア", blank=True)
    current_avatar = models.CharField('現在のアバター', max_length=100, default="初期アバター", blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'プロフィール'
        verbose_name_plural = 'プロフィール'


# 3. 投稿モデル
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    content = models.TextField('内容', max_length=140)

    # 🔮 裏技：投稿画像もデータベースに直接保存
    image = models.TextField('画像', blank=True, null=True)

    subject = models.CharField('科目', max_length=50, default="その他")
    study_minutes = models.IntegerField('勉強時間(分)', default=0)

    # ⚡ 爆速化：db_index=True を追加し、数万件になっても並び替えを一瞬にする
    created_at = models.DateTimeField('作成日時', auto_now_add=True, db_index=True)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True, verbose_name='いいねしたユーザー')
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='リプライ先')

    def __str__(self):
        return f'{self.user.username}: {self.content[:10]}'

    class Meta:
        verbose_name = '投稿'
        verbose_name_plural = '投稿'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]


# 4. コメントモデル
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='投稿')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    text = models.TextField('コメント', max_length=100)
    created_at = models.DateTimeField('作成日時', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]


# 5. 通知モデル
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='受信者')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name='送信者')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name='関連投稿')
    notification_type = models.CharField('通知タイプ', max_length=20,
                                         choices=[('like', 'いいね'), ('reply', 'リプライ'), ('follow', 'フォロー')])
    is_read = models.BooleanField('既読', default=False)
    created_at = models.DateTimeField('作成日時', auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username} ({self.notification_type})"

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]


class UserLoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_sessions', verbose_name='ユーザー')
    login_at = models.DateTimeField('ログイン日時', auto_now_add=True, db_index=True)
    last_seen_at = models.DateTimeField('最終アクセス日時', auto_now=True, db_index=True)
    logout_at = models.DateTimeField('ログアウト日時', null=True, blank=True)
    ip_address = models.GenericIPAddressField('IPアドレス', null=True, blank=True)
    user_agent = models.TextField('ユーザーエージェント', blank=True)

    def __str__(self):
        return f"{self.user.username} {self.login_at:%Y-%m-%d %H:%M}"

    class Meta:
        verbose_name = 'ログインセッション'
        verbose_name_plural = 'ログインセッション'
        ordering = ['-login_at']
        indexes = [
            models.Index(fields=['user', '-login_at']),
            models.Index(fields=['logout_at', '-last_seen_at']),
        ]


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

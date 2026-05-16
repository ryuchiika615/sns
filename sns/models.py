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


# 2. 投稿モデル
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=140)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    study_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def __str__(self):
        return f'{self.user.username}: {self.content[:10]}'


# 3. コメントモデル
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


# 4. プロフィール（中二病アイコンフィールドを新規追加！）
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    icon = models.ImageField(upload_to='icons/', default='icons/default.png', blank=True)
    points = models.IntegerField(default=0)
    items = models.ManyToManyField(GachaItem, blank=True)
    current_title = models.CharField(max_length=100, default="新人エンジニア", blank=True)

    # ★ ここを新規追加！今セットしているアイコンスキンを保存する場所です
    current_avatar = models.CharField(max_length=100, default="初期アバター", blank=True)

    def __str__(self):
        return self.user.username


# 5. ユーザー作成時にプロフィールを自動作成する設定
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
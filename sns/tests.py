from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Comment, GachaItem, Notification, Post, Profile


class ProfileModelTest(TestCase):
    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user(username="testuser", password="pass123")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str(self):
        user = User.objects.create_user(username="testuser", password="pass123")
        self.assertEqual(str(user.profile), "testuser")


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="poster", password="pass123")

    def test_create_post(self):
        post = Post.objects.create(
            user=self.user, content="Test study post", subject="数学", study_minutes=30
        )
        self.assertEqual(post.study_minutes, 30)
        self.assertEqual(str(post), "poster: Test study")

    def test_post_ordering(self):
        Post.objects.create(user=self.user, content="First", study_minutes=10)
        posts = Post.objects.all()
        self.assertEqual(posts.count(), 1)


class GachaItemModelTest(TestCase):
    def test_gacha_item_creation(self):
        item = GachaItem.objects.create(name="テスト称号", rarity="SSR")
        self.assertEqual(str(item), "[SSR] テスト称号")


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="commenter", password="pass123")
        self.post = Post.objects.create(user=self.user, content="Test")

    def test_create_comment(self):
        comment = Comment.objects.create(post=self.post, user=self.user, text="Nice!")
        self.assertEqual(comment.text, "Nice!")


class NotificationModelTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="alice", password="pass123")
        self.u2 = User.objects.create_user(username="bob", password="pass123")

    def test_create_notification(self):
        n = Notification.objects.create(
            recipient=self.u1, sender=self.u2, notification_type="follow"
        )
        self.assertFalse(n.is_read)
        self.assertEqual(str(n), "bob -> alice (follow)")


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")

    def test_login_required(self):
        response = self.client.get(reverse("index"))
        self.assertRedirects(response, "/login/?next=/")

    def test_logged_in_access(self):
        self.client.login(username="testuser", password="pass123")
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        self.client.login(username="testuser", password="pass123")
        response = self.client.post(
            reverse("index"),
            {
                "content": "勉強したよ",
                "subject": "数学",
                "study_minutes": "60",
            },
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().study_minutes, 60)


class SignupViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_page(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_signup_success(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "securepass123",
                "password2": "securepass123",
            },
        )
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(User.objects.filter(username="newuser").exists())


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass123")

    def test_login_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "pass123"}
        )
        self.assertRedirects(response, reverse("index"))


class HealthCheckTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

from django.urls import path
from . import views

urlpatterns = [
    path("healthz/", views.health_check, name="health_check"),
    path("", views.index, name="index"),
    path("gacha/", views.gacha, name="gacha"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("signup/", views.signup, name="signup"),
    # ★ 管理者は自動で管理画面に飛ぶカスタムログイン
    path(
        "login/",
        views.CustomLoginView.as_view(template_name="sns/login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("like/<int:post_id>/", views.like_post, name="like_post"),
    path("like/<int:post_id>/ajax/", views.like_post_ajax, name="like_post_ajax"),
    path("comment/<int:post_id>/ajax/", views.comment_ajax, name="comment_ajax"),
    path("user/<str:username>/", views.user_profile, name="user_profile"),
    path("follow/<str:username>/", views.toggle_follow, name="toggle_follow"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("analytics/", views.analytics_view, name="analytics"),
    path("rankings/", views.rankings_view, name="rankings"),
    path(
        "admin/login-activity/", views.admin_login_activity, name="admin_login_activity"
    ),
]

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('gacha/', views.gacha, name='gacha'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('signup/', views.signup, name='signup'),

    # ★ 新規追加：ログイン画面への道
    path('login/', auth_views.LoginView.as_view(template_name='sns/login.html'), name='login'),

    path('logout/', views.logout_view, name='logout'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('rankings/', views.rankings_view, name='rankings'),
    path('admin/login-activity/', views.admin_login_activity, name='admin_login_activity'),
]

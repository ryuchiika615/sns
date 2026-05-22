from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('gacha/', views.gacha, name='gacha'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('notifications/', views.notifications_view, name='notifications'),

    # ★ 新規追加：レポート（分析）画面
    path('analytics/', views.analytics_view, name='analytics'),
]
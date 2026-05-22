from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('gacha/', views.gacha, name='gacha'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),

    # ★ 新規追加：プロフィール画面とフォロー機能
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
]
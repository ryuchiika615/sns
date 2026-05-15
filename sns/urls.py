from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='sns/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    # ★ ここが足りていなかったはず！ガチャへの道を追加します
    path('gacha/', views.gacha, name='gacha'),
]
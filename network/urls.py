from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("submit_post", views.submit_post, name="submit_post"),
    path("posts", views.get_posts, name="get_post"),
    path("post/<str:id>", views.modify_post, name="modify_post"),
    path("post/<str:id>/like", views.like_post, name="like_post"),
    path("user/<str:username>", views.get_user_profile, name="profile"),
    path("user/<str:username>/follow", views.follow, name="follow_user"),
]

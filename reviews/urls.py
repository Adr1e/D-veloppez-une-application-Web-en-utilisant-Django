from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Auth & flux
    path("", views.feed, name="feed"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.signin, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("accueil/", views.feed, name="home"),

    # Mes posts
    path("mes-posts/", views.my_posts, name="my_posts"),

    # Tickets CRUD
    path("tickets/nouveau/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/modifier/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:pk>/supprimer/", views.ticket_delete, name="ticket_delete"),

    # Reviews CRUD
    path("tickets/<int:ticket_id>/critique/nouvelle/", views.review_create_from_ticket, name="review_create_from_ticket"),
    path("critiques/<int:pk>/modifier/", views.review_update, name="review_update"),
    path("critiques/<int:pk>/supprimer/", views.review_delete, name="review_delete"),

    # Abonnements
    path("abonnements/", views.subscriptions, name="subscriptions"),
    path("abonnements/<int:user_id>/desabonner/", views.unfollow, name="unfollow"),
    
]

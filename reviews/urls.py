from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Authentification & flux
    path("", views.feed, name="feed"),  # page d’accueil : flux principal
    path("signup/", views.signup, name="signup"),  # inscription
    path("login/", views.signin, name="login"),    # connexion
    path("logout/", LogoutView.as_view(), name="logout"),  # déconnexion

    path("accueil/", views.feed, name="home"),  # alias de la page d’accueil

    # Mes posts (tickets + critiques de l’utilisateur courant)
    path("mes-posts/", views.my_posts, name="my_posts"),

    # Tickets CRUD
    path("tickets/nouveau/", views.ticket_create, name="ticket_create"),  # création ticket
    path("tickets/<int:pk>/modifier/", views.ticket_update, name="ticket_update"),  # modification ticket
    path("tickets/<int:pk>/supprimer/", views.ticket_delete, name="ticket_delete"),  # suppression ticket
    path("critiques/nouvelle/", views.review_create_combo, name="review_create_combo"),  
    # création combinée ticket + critique

    # Reviews CRUD
    path("tickets/<int:ticket_id>/critique/nouvelle/", views.review_create_from_ticket, name="review_create_from_ticket"),  
    # créer une critique en réponse à un ticket
    path("critiques/<int:pk>/modifier/", views.review_update, name="review_update"),  # modification critique
    path("critiques/<int:pk>/supprimer/", views.review_delete, name="review_delete"),  # suppression critique

    # Abonnements
    path("abonnements/", views.subscriptions, name="subscriptions"),  # gestion abonnements
    path("abonnements/<int:user_id>/desabonner/", views.unfollow, name="unfollow"),  # se désabonner d’un utilisateur
]

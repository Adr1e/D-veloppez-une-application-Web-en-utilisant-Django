# reviews/models.py
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F


# Modèle Ticket : représente une demande de critique
class Ticket(models.Model):
    title = models.CharField(max_length=128)  # titre du ticket (obligatoire)
    description = models.TextField(max_length=2048, blank=True)  # description (facultative)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    # auteur du ticket (lié à l'utilisateur connecté)

    image = models.ImageField(upload_to="tickets/", null=True, blank=True)  
    # image optionnelle liée au ticket, stockée dans /media/tickets/

    time_created = models.DateTimeField(auto_now_add=True)  
    # date/heure automatique lors de la création

    def __str__(self):
        # représentation textuelle pratique pour l’admin Django
        return f"Ticket<{self.id}> {self.title}"


# Modèle Review : représente une critique faite sur un ticket
class Review(models.Model):
    ticket = models.ForeignKey(
        to=Ticket, on_delete=models.CASCADE, related_name="reviews"
    )  
    # critique rattachée à un ticket donné

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )  
    # note comprise entre 0 et 5

    headline = models.CharField(max_length=128)  # titre court de la critique
    body = models.TextField(max_length=8192, blank=True)  # texte principal (facultatif)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    # auteur de la critique

    time_created = models.DateTimeField(auto_now_add=True)  
    # date/heure automatique lors de la création

    class Meta:
        # un même utilisateur ne peut poster qu’une seule critique par ticket
        constraints = [
            models.UniqueConstraint(
                fields=["ticket", "user"], name="unique_review_per_user_and_ticket"
            )
        ]

    def __str__(self):
        return f"Review<{self.id}> {self.headline} ({self.rating}/5)"


# Modèle UserFollows : représente une relation de suivi entre deux utilisateurs
class UserFollows(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )  
    # l'utilisateur qui suit quelqu'un

    followed_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followed_by",
    )  
    # l'utilisateur qui est suivi

    class Meta:
        unique_together = ("user", "followed_user")  
        # empêche de suivre deux fois la même personne
        constraints = [
            models.CheckConstraint(
                check=~Q(user=F("followed_user")), name="prevent_self_follow"
            )
        ]  
        # empêche un utilisateur de se suivre lui-même

    def __str__(self):
        return f"{self.user} → {self.followed_user}"

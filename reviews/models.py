from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F

# Billet (demande de critique) 
class Ticket(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="tickets/", null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket<{self.id}> {self.title}"

# Commentaire / Critique en réponse à un ticket 
class Review(models.Model):
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Une seule critique par ticket 
        constraints = [
            models.UniqueConstraint(fields=["ticket"], name="unique_review_per_ticket")
        ]

    def __str__(self):
        return f"Review<{self.id}> {self.headline} ({self.rating}/5)"

# Suivi d’utilisateurs 
class UserFollows(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    followed_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followed_by"
    )

    class Meta:
        unique_together = ("user", "followed_user")
        constraints = [
            # empêche de se suivre soi-même
            models.CheckConstraint(check=~Q(user=F("followed_user")), name="prevent_self_follow")
        ]

    def __str__(self):
        return f"{self.user} → {self.followed_user}"

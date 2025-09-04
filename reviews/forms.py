from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Ticket, Review

# --- Auth ---
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

# --- Tickets ---
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("title", "description", "image")

# --- Reviews ---
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("headline", "rating", "body")
        widgets = {"rating": forms.NumberInput(attrs={"min": 0, "max": 5})}

# --- Abonnements ---
class FollowForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur à suivre",
        help_text="Saisissez le nom d’utilisateur exact."
    )

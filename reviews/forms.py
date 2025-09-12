from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Ticket, Review

# Formulaire d'inscription basé sur le formulaire intégré de Django
class SignUpForm(UserCreationForm):
    class Meta:
        model = User  # modèle utilisateur par défaut de Django
        fields = ("username", "password1", "password2")  # champs affichés dans le formulaire


# Formulaire de création et modification de tickets
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket  # modèle Ticket défini dans models.py
        fields = ("title", "description", "image")  # champs inclus dans le formulaire


# Formulaire de création et modification de critiques
class ReviewForm(forms.ModelForm):
    # Définition des choix pour la note (0 à 5) sous forme de boutons radio
    RATING_CHOICES = [(i, str(i)) for i in range(6)]
    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES,       # options disponibles (0, 1, 2, 3, 4, 5)
        coerce=int,                   # conversion automatique en entier
        widget=forms.RadioSelect,     # affichage en boutons radio
        label="Note (0–5)",           # étiquette affichée dans le formulaire
    )

    class Meta:
        model = Review  # modèle Review défini dans models.py
        fields = ("headline", "rating", "body")  # champs inclus dans le formulaire


# Formulaire pour suivre un utilisateur
class FollowForm(forms.Form):
    username = forms.CharField(
        max_length=150,  # longueur max du nom d'utilisateur
        label="Nom d'utilisateur à suivre",  # étiquette affichée
        help_text="Saisissez le nom d’utilisateur exact."  # aide affichée sous le champ
    )

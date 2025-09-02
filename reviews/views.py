from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import SignUpForm

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Bienvenue ! Votre compte est créé.")
            return redirect("feed")  # en cas de succès, on redirige réponse 302
        else:
            # en cas d'erreur ça boucle réponse 200 
            print("SIGNUP ERRORS:", form.errors.as_json())
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def signin(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, "Connexion réussie.")
            return redirect("feed")
    else:
        form = AuthenticationForm(request)
    return render(request, "signin.html", {"form": form})

@login_required
def feed(request):
    return render(request, "feed.html")

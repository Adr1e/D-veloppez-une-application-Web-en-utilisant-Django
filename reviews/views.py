from itertools import chain

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import CharField, Q, Value
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SignUpForm, TicketForm, ReviewForm, FollowForm
from .models import Ticket, Review, UserFollows

# ---------- Auth ----------
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Bienvenue ! Votre compte est créé.")
            return redirect("feed")
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
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

# ---------- Helpers Flux ----------
def _following_ids(user):
    return UserFollows.objects.filter(user=user).values_list("followed_user_id", flat=True)

def get_users_viewable_tickets(user):
    return (
        Ticket.objects
        .filter(Q(user__in=_following_ids(user)) | Q(user=user))
        .select_related("user")
        .prefetch_related("reviews")
    )

def get_users_viewable_reviews(user):
    base = Review.objects.filter(Q(user__in=_following_ids(user)) | Q(user=user))
    extra = Review.objects.filter(ticket__user=user)  # critiques sur MES tickets
    return (base | extra).select_related("user", "ticket", "ticket__user").distinct()

# ---------- Flux ----------
@login_required
def feed(request):
    reviews = get_users_viewable_reviews(request.user).annotate(content_type=Value("REVIEW", CharField()))
    tickets = get_users_viewable_tickets(request.user).annotate(content_type=Value("TICKET", CharField()))
    posts = sorted(chain(reviews, tickets), key=lambda p: p.time_created, reverse=True)
    return render(request, "feed.html", {"posts": posts})

# ---------- Tickets: create / update / delete ----------
@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, "Ticket créé.")
            return redirect("my_posts")
    else:
        form = TicketForm()
    return render(request, "ticket_form.html", {"form": form, "mode": "create"})

@login_required
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket modifié.")
            return redirect("my_posts")
    else:
        form = TicketForm(instance=ticket)
    return render(request, "ticket_form.html", {"form": form, "mode": "update", "ticket": ticket})

@login_required
def ticket_delete(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    if request.method == "POST":
        ticket.delete()
        messages.success(request, "Ticket supprimé.")
        return redirect("my_posts")
    return render(request, "confirm_delete.html", {"object": ticket, "type": "ticket"})

# ---------- Reviews: create/update/delete ----------
@login_required
def review_create_from_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if ticket.reviews.exists():
        messages.error(request, "Une critique existe déjà pour ce ticket.")
        return redirect("feed")
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.ticket = ticket
            review.save()
            messages.success(request, "Critique publiée.")
            return redirect("my_posts")
    else:
        form = ReviewForm()
    return render(request, "review_form.html", {"form": form, "ticket": ticket, "mode": "create"})

@login_required
def review_update(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Critique modifiée.")
            return redirect("my_posts")
    else:
        form = ReviewForm(instance=review)
    return render(request, "review_form.html", {"form": form, "ticket": review.ticket, "mode": "update"})

@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    if request.method == "POST":
        review.delete()
        messages.success(request, "Critique supprimée.")
        return redirect("my_posts")
    return render(request, "confirm_delete.html", {"object": review, "type": "review"})

# ---------- Mes posts ----------
@login_required
def my_posts(request):
    my_tickets = Ticket.objects.filter(user=request.user).order_by("-time_created")
    my_reviews = Review.objects.filter(user=request.user).select_related("ticket").order_by("-time_created")
    return render(request, "my_posts.html", {"tickets": my_tickets, "reviews": my_reviews})

# ---------- Abonnements (liste + ajout + suppression) ----------
@login_required
def subscriptions(request):
    """Liste mes suivis/abonnés + formulaire pour suivre quelqu'un par username."""
    following = UserFollows.objects.filter(user=request.user).select_related("followed_user")
    followers = UserFollows.objects.filter(followed_user=request.user).select_related("user")

    if request.method == "POST":
        form = FollowForm(request.POST)
        if form.is_valid():
            target_username = form.cleaned_data["username"].strip()
            User = get_user_model()
            try:
                target = User.objects.get(username=target_username)
            except User.DoesNotExist:
                messages.error(request, "Utilisateur introuvable.")
                return redirect("subscriptions")

            if target == request.user:
                messages.error(request, "Vous ne pouvez pas vous suivre vous-même.")
                return redirect("subscriptions")

            obj, created = UserFollows.objects.get_or_create(user=request.user, followed_user=target)
            if created:
                messages.success(request, f"Vous suivez {target.username}.")
            else:
                messages.info(request, f"Vous suivez déjà {target.username}.")
            return redirect("subscriptions")
    else:
        form = FollowForm()

    return render(
        request,
        "subscriptions.html",
        {"following": following, "followers": followers, "form": form},
    )

@login_required
def unfollow(request, user_id):
    """Suppression d'un abonnement via POST uniquement."""
    if request.method == "POST":
        UserFollows.objects.filter(user=request.user, followed_user_id=user_id).delete()
        messages.success(request, "Désabonnement effectué.")
    return redirect("subscriptions")

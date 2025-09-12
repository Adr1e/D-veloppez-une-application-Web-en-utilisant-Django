from itertools import chain

from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import CharField, Q, Value, Exists, OuterRef
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SignUpForm, TicketForm, ReviewForm, FollowForm
from .models import Ticket, Review, UserFollows


# Authentification
def signup(request):
    # Inscription utilisateur avec connexion automatique après création
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # connexion immédiate
            messages.success(request, "Bienvenue ! Votre compte est créé.")
            return redirect("feed")
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def signin(request):
    # Connexion utilisateur avec AuthenticationForm intégré Django
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

# Fonctions utilitaires
def _following_ids(user):
    # Renvoie les IDs des utilisateurs suivis par l’utilisateur courant
    return UserFollows.objects.filter(user=user).values_list("followed_user_id", flat=True)


def get_users_viewable_tickets(user):
    # Tickets visibles : ceux de l’utilisateur et de ses abonnements
    # Annotés avec un booléen has_reviewed (si l’utilisateur a déjà critiqué le ticket)
    user_review_exists = Review.objects.filter(ticket=OuterRef("pk"), user=user)
    return (
        Ticket.objects
        .filter(Q(user__in=_following_ids(user)) | Q(user=user))
        .select_related("user")
        .prefetch_related("reviews")
        .annotate(content_type=Value("TICKET", CharField()))
        .annotate(has_reviewed=Exists(user_review_exists))
    )


def get_users_viewable_reviews(user):
    # Critiques visibles : celles de l’utilisateur, de ses abonnements et sur ses tickets
    base = Review.objects.filter(Q(user__in=_following_ids(user)) | Q(user=user))
    extra = Review.objects.filter(ticket__user=user)
    return (base | extra).select_related("user", "ticket", "ticket__user").distinct()


# Flux principal
@login_required
def feed(request):
    # Combine tickets et critiques visibles puis les trie du plus récent au plus ancien
    reviews = get_users_viewable_reviews(request.user).annotate(content_type=Value("REVIEW", CharField()))
    tickets = get_users_viewable_tickets(request.user)
    posts = sorted(chain(reviews, tickets), key=lambda p: p.time_created, reverse=True)
    return render(request, "feed.html", {"posts": posts})

# Tickets
@login_required
def ticket_create(request):
    # Création d’un ticket par l’utilisateur connecté
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
    # Modification d’un ticket appartenant à l’utilisateur
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
    # Suppression d’un ticket appartenant à l’utilisateur
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    if request.method == "POST":
        ticket.delete()
        messages.success(request, "Ticket supprimé.")
        return redirect("my_posts")
    return render(request, "confirm_delete.html", {"object": ticket, "type": "ticket"})


# Reviews
@login_required
def review_create_from_ticket(request, ticket_id):
    # Création d’une critique en réponse à un ticket
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Vérification : pas de critique en double par le même utilisateur
    if Review.objects.filter(ticket=ticket, user=request.user).exists():
        messages.error(request, "Vous avez déjà publié une critique pour ce ticket.")
        return redirect("feed")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                review = form.save(commit=False)
                review.user = request.user
                review.ticket = ticket
                review.save()
            except IntegrityError:
                # Sécurité : si la contrainte d’unicité de la base bloque
                messages.error(request, "Impossible d’enregistrer : une contrainte d’unicité empêche plusieurs critiques par ticket. Vérifiez que les migrations sont à jour.")
                return redirect("feed")
            messages.success(request, "Critique publiée.")
            return redirect("my_posts")
    else:
        form = ReviewForm()
    return render(request, "review_form.html", {"form": form, "ticket": ticket, "mode": "create"})


@login_required
def review_update(request, pk):
    # Modification d’une critique appartenant à l’utilisateur
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
    # Suppression d’une critique appartenant à l’utilisateur
    review = get_object_or_404(Review, pk=pk, user=request.user)
    if request.method == "POST":
        review.delete()
        messages.success(request, "Critique supprimée.")
        return redirect("my_posts")
    return render(request, "confirm_delete.html", {"object": review, "type": "review"})


# Mes posts
@login_required
def my_posts(request):
    # Affiche mes tickets et mes critiques séparément
    # Les tickets sont annotés pour savoir si j’ai déjà critiqué dessus
    user_review_exists = Review.objects.filter(ticket=OuterRef("pk"), user=request.user)
    my_tickets = (
        Ticket.objects
        .filter(user=request.user)
        .order_by("-time_created")
        .annotate(has_reviewed=Exists(user_review_exists))
    )
    my_reviews = Review.objects.filter(user=request.user).select_related("ticket").order_by("-time_created")
    return render(request, "my_posts.html", {"tickets": my_tickets, "reviews": my_reviews})


# Abonnements
@login_required
def subscriptions(request):
    # Affiche la liste des abonnements et abonnés
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
    # Permet de se désabonner d’un utilisateur
    if request.method == "POST":
        UserFollows.objects.filter(user=request.user, followed_user_id=user_id).delete()
        messages.success(request, "Désabonnement effectué.")
    return redirect("subscriptions")

# Ticket + Review combinés
@login_required
@require_http_methods(["GET", "POST"])
def review_create_combo(request):
    """
    Création combinée d’un Ticket et d’une Review en une seule étape.
    """
    tform = TicketForm(request.POST or None, request.FILES or None)
    rform = ReviewForm(request.POST or None)

    if request.method == "POST":
        if tform.is_valid() and rform.is_valid():
            try:
                # Création du ticket
                ticket = tform.save(commit=False)
                ticket.user = request.user
                ticket.save()

                # Création de la critique liée au ticket
                review = rform.save(commit=False)
                review.user = request.user
                review.ticket = ticket
                review.save()
            except IntegrityError:
                # Sécurité : si la base empêche plusieurs critiques sur un même ticket
                messages.error(request, "Impossible d’enregistrer : contrainte d’unicité violée. Vérifiez vos migrations.")
                return redirect("feed")
            messages.success(request, "Ticket et critique publiés.")
            return redirect("my_posts")
        messages.error(request, "Veuillez corriger les erreurs des formulaires.")
    return render(request, "review_create_combo.html", {"tform": tform, "rform": rform})

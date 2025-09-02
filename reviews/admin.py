from django.contrib import admin
from .models import Ticket, Review, UserFollows

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "time_created")
    search_fields = ("title", "user__username")
    ordering = ("-time_created",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "headline", "rating", "user", "ticket", "time_created")
    search_fields = ("headline", "user__username", "ticket__title")
    ordering = ("-time_created",)

@admin.register(UserFollows)
class UserFollowsAdmin(admin.ModelAdmin):
    list_display = ("user", "followed_user")
    search_fields = ("user__username", "followed_user__username")

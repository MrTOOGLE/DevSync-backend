from django.contrib import admin
from .models import Voting, VotingOption, VotingOptionChoice, VotingComment


@admin.register(Voting)
class VotingAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'creator', 'date_started', 'end_date', 'project')
    list_display_links = ('title', )
    list_per_page = 10

    list_filter = ['status']
    search_fields = ['project', 'title']
    actions = []

    save_on_top = True


@admin.register(VotingOption)
class VotingOptionAdmin(admin.ModelAdmin):
    list_display = ('voting', 'body')
    list_display_links = ('voting',)
    search_fields = ['voting', ]

    list_per_page = 10
    actions = []

    save_on_top = True


@admin.register(VotingOptionChoice)
class VotingOptionChoiceAdmin(admin.ModelAdmin):
    list_display = ('voting_option', 'user')
    list_display_links = ('voting_option', )
    search_fields = ('voting_option__startswith', 'user')

    list_per_page = 10
    actions = []

    save_on_top = True


@admin.register(VotingComment)
class VotingCommentAdmin(admin.ModelAdmin):
    list_display = ('voting', 'sender', 'date_sent')
    list_display_links = ('voting',)
    search_fields = ('voting__startswith', 'sender__username')

    list_per_page = 10
    actions = []

    save_on_top = True

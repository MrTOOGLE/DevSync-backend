from django.contrib.auth import get_user_model
from django.db import models

from projects.models import Project


User = get_user_model()


class Voting(models.Model):
    class Status(models.TextChoices):
        NEW = 'new','Новое'
        UNDER_REVIEW = 'under_review', 'На рассмотрении'
        ACCEPTED = 'accepted', 'Принято'
        REJECTED = 'rejected', 'Отклонено'

    title = models.CharField(max_length=150)
    body = models.CharField(max_length=2000)
    date_started = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    creator = models.ForeignKey(User, related_name='created_votings', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    project = models.ForeignKey(Project, related_name='votings', on_delete=models.CASCADE)

    def __str__(self):
        return f"Voting: {self.title} (Status: {self.status})"


class VotingOption(models.Model):
    voting = models.ForeignKey(Voting, related_name='options', on_delete=models.CASCADE)
    body = models.CharField(max_length=250)

    def __str__(self):
        return f"Option for {self.voting.title}: {self.body}"


class VotingOptionChoice(models.Model):
    voting_option = models.ForeignKey(VotingOption, related_name='choices', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='voting_choices', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['voting_option', 'user'], name='unique_user_choices')
        ]

    def __str__(self):
        return f"User {self.user} selected option: {self.voting_option.body[:20]}..."


class VotingComment(models.Model):
    voting = models.ForeignKey(Voting, related_name='comments', on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)
    body = models.CharField(max_length=3000)
    sender = models.ForeignKey(User, related_name='voting_comments', on_delete=models.SET_NULL, null=True)
    parent_comment = models.ForeignKey('self', related_name='replies', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Comment by {self.sender}: {self.body[:20]}..."

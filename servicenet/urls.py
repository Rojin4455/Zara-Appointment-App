from django.urls import path
from servicenet.views import *

urlpatterns = [
    path("webhook",GhlWebhookView.as_view() , name="webhook"),
    path("refresh-users", HandleUsersView.as_view(), name="handle-refresh")
]
from core.views import *
from django.urls import path

urlpatterns = [
    path('onboard/', onboard),
    path("auth/connect/", auth_connect, name="oauth_connect"),
    path("auth/tokens/", tokens, name="oauth_tokens"),
    path("auth/callback/", callback, name="oauth_callback"),
    path('get-token/', get_token),

    path('', admin_login_view, name='admin_login'),
    path('admin-login/', admin_login_view, name='admin_login'),
    path('admin-logout/', admin_logout_view, name='admin_logout'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path("location-users/<str:location_id>/", location_users_ajax, name='location_users_ajax')
]
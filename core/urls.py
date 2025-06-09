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
    path("location-users/<str:location_id>/", location_users_ajax, name='location_users_ajax'),


    path('update-user-calendar/<str:user_id>/', update_user_calendar, name='update_user_calendar'),
    
    # Optional: Bulk update calendar IDs
    path('bulk-update-calendars/', bulk_update_calendars, name='bulk_update_calendars'),
    
    # Optional: Get calendar statistics
    path('calendar-stats/', get_calendar_stats, name='get_calendar_stats'),
    path('calendar-stats/<str:location_id>/', get_calendar_stats, name='get_location_calendar_stats'),

]
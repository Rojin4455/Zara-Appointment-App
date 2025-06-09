from decouple import config
import requests
from django.http import JsonResponse
import json
from django.shortcuts import redirect, render
from core.models import GHLAuthCredentials
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from core.helpers import get_location_data
from servicenet.models import GHLUser



GHL_CLIENT_ID = config("GHL_CLIENT_ID")
GHL_CLIENT_SECRET = config("GHL_CLIENT_SECRET")
GHL_REDIRECTED_URI = config("GHL_REDIRECTED_URI")
TOKEN_URL = "https://services.leadconnectorhq.com/oauth/token"
SCOPE = config("SCOPE")


def onboard(request):
    return render(request,'onboard.html')


def auth_connect(request):
    auth_url = ("https://marketplace.gohighlevel.com/oauth/chooselocation?response_type=code&"
                f"redirect_uri={GHL_REDIRECTED_URI}&"
                f"client_id={GHL_CLIENT_ID}&"
                f"scope={SCOPE}"
                )
    return redirect(auth_url)



def callback(request):
    
    code = request.GET.get('code')

    if not code:
        return JsonResponse({"error": "Authorization code not received from OAuth"}, status=400)

    return redirect(f'{config("BASE_URI")}/auth/tokens?code={code}')


def tokens(request):
    authorization_code = request.GET.get("code")

    if not authorization_code:
        return JsonResponse({"error": "Authorization code not found"}, status=400)

    data = {
        "grant_type": "authorization_code",
        "client_id": GHL_CLIENT_ID,
        "client_secret": GHL_CLIENT_SECRET,
        "redirect_uri": GHL_REDIRECTED_URI,
        "code": authorization_code,
    }

    response = requests.post(TOKEN_URL, data=data)

    try:
        response_data = response.json()
        if not response_data:
            return
        print("response.data: ", response_data)

        if not response_data.get('access_token'):
            return render(request, 'admin_auth/dashboard.html', context={
                "message": "Invalid JSON response from API",
                "status_code": response.status_code,
                "response_text": response.text[:400],
                "ghl_credentials": GHLAuthCredentials.objects.all().values("user_id","user_type", "company_id", "location_id", "location_name")
            }, status=400)
        
        location_data = get_location_data(location_id=response_data.get("locationId"), access_token=response_data.get("access_token"))

        obj, created = GHLAuthCredentials.objects.update_or_create(
            location_id= response_data.get("locationId"),
            defaults={
                "access_token": response_data.get("access_token"),
                "refresh_token": response_data.get("refresh_token"),
                "expires_in": response_data.get("expires_in"),
                "scope": response_data.get("scope"),
                "user_type": response_data.get("userType"),
                "company_id": response_data.get("companyId"),
                "user_id":response_data.get("userId"),
                "location_name": location_data['location']['name']
            }
        )

        
        return render(request, 'admin_auth/dashboard.html', context = {
            "message": "Authentication successful",
            "access_token": response_data.get('access_token'),
            "token_stored": True,
            "ghl_credentials": GHLAuthCredentials.objects.all().values("user_id","user_type", "company_id", "location_id", "location_name")
        })
        
    except requests.exceptions.JSONDecodeError:
        return render(request, 'admin_auth/dashboard.html', context={
            "error": "Invalid JSON response from API",
            "status_code": response.status_code,
            "response_text": response.text[:500],
            "ghl_credentials": GHLAuthCredentials.objects.all().values("user_id","user_type", "company_id", "location_id", "location_name")
        }, status=500)
    


def get_token(request):
    location_id = request.GET.get('locationId')
    if not location_id:
        return JsonResponse({'error': 'Missing locationId in query params'}, status=400)
    try:
        token = GHLAuthCredentials.objects.get(location_id=location_id)
        return JsonResponse({'access_token': token.access_token})
    except GHLAuthCredentials.DoesNotExist:
        return JsonResponse({'error': 'Token not found for the given locationId'}, status=404)




def is_admin_user(user):
    """Check if user is admin (staff or superuser)"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)




def is_admin_user(user):
    """Check if user is admin (staff or superuser)"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@csrf_protect
@never_cache
def admin_login_view(request):
    """Admin login view - only allows staff/superuser access"""
    
    # If user is already authenticated and is admin, redirect to dashboard
    if request.user.is_authenticated and is_admin_user(request.user):
        return redirect('admin_dashboard')
    
    # If user is authenticated but not admin, show error
    if request.user.is_authenticated and not is_admin_user(request.user):
        messages.error(request, 'Access denied. Admin privileges required.')
        logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if user has admin privileges
                if is_admin_user(user):
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect to next page or dashboard
                    next_page = request.GET.get('next', 'admin_dashboard')
                    return redirect(next_page)
                else:
                    messages.error(request, 'Access denied. Admin privileges required.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'admin_auth/login.html')


@user_passes_test(is_admin_user, login_url='admin_login')
def admin_logout_view(request):
    """Admin logout view"""
    username = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {username}! You have been logged out successfully.')
    return redirect('admin_login')


class AdminDashboardView(UserPassesTestMixin, TemplateView):
    """Admin dashboard - only accessible to staff/superusers"""
    template_name = 'admin_auth/dashboard.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Admin privileges required.')
        return redirect('admin_login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        
        # Get GHL credentials data with user counts
        ghl_credentials = GHLAuthCredentials.objects.all().values(
            "user_id", "user_type", "company_id", "location_id", "location_name"
        )
        
        # Add user count for each location
        credentials_with_counts = []
        for credential in ghl_credentials:
            credential_dict = dict(credential)
            if credential['location_id']:
                user_count = GHLUser.objects.filter(location_id=credential['location_id']).count()
                credential_dict['user_count'] = user_count
            else:
                credential_dict['user_count'] = 0
            credentials_with_counts.append(credential_dict)
        
        context['ghl_credentials'] = credentials_with_counts
        context['total_connections'] = len(credentials_with_counts)
        context['active_locations'] = sum(1 for c in credentials_with_counts if c['location_id'])
        context['companies_count'] = len(set(c['company_id'] for c in credentials_with_counts if c['company_id']))
        
        return context

def location_users_ajax(request, location_id):
    """AJAX endpoint to fetch users for a specific location"""
    if not is_admin_user(request.user):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        users = GHLUser.objects.filter(location_id=location_id).values(
            'user_id', 'first_name', 'last_name', 'name', 'email', 'phone', 'calendar_id'
        )
        
        users_list = []
        for user in users:
            user_dict = dict(user)
            # Ensure phone is not None
            user_dict['phone'] = user_dict['phone'] or 'N/A'
            users_list.append(user_dict)
        
        return JsonResponse({
            'users': users_list,
            'location_id': location_id,
            'total_users': len(users_list)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@method_decorator(user_passes_test(is_admin_user, login_url='admin_login'), name='dispatch')
class AdminProtectedView(TemplateView):
    """Base view for admin-only pages"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from servicenet.services import pull_users
from servicenet.models import GHLUser
from core.models import GHLAuthCredentials
import requests
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import pytz
from servicenet.models import GHLAppointment



BST = pytz.timezone("Europe/London")

@method_decorator(csrf_exempt, name='dispatch')
class GhlWebhookView(View):
    def post(self, request):
        try:
            webhook_data = json.loads(request.body)
            event_type = webhook_data.get("type")
            token = GHLAuthCredentials.objects.get(location_id = webhook_data.get("locationId"))

            if event_type == "TaskCreate":
                self.handle_task_create(webhook_data, token)

            elif event_type == "TaskDelete":
                self.handle_task_delete(webhook_data, token)

            return JsonResponse({"message": "Handled"}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def handle_task_create(self, data, token):
        task_id = data["id"]
        contact_id = data["contactId"]
        assigned_to = data["assignedTo"]
        location_id = data["locationId"]
        title = data["title"]
        description = data["body"]
        calendar_id = self.get_calendar_id(assigned_to, location_id, token)
        
        start_time_utc = parse_datetime(data["dueDate"])
        start_time_bst = start_time_utc.astimezone(BST)
        end_time_bst = start_time_bst + timedelta(minutes=30)

        payload = {
            "title": title,
            "meetingLocationType": "custom",
            "meetingLocationId": "default",
            "overrideLocationConfig": True,
            "appointmentStatus": "new",
            "assignedUserId": assigned_to,
            "address": "Zoom",
            "ignoreDateRange": False,
            "toNotify": False,
            "ignoreFreeSlotValidation": True,
            "calendarId": calendar_id,
            "locationId": location_id,
            "contactId": contact_id,
            "startTime": start_time_bst.isoformat(),
            "endTime": end_time_bst.isoformat()
        }

        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Version": "2021-04-15"
        }

        response = requests.post(
            "https://services.leadconnectorhq.com/calendars/events/appointments",
            headers=headers,
            json=payload
        )

        if response.status_code == 201:
            ghl_data = response.json()
            GHLAppointment.objects.create(
                ghl_appointment_id=ghl_data.get("id"),
                ghl_task_id=task_id,
                contact_id=contact_id,
                assigned_to=assigned_to,
                calendar_id=calendar_id,
                location_id=location_id,
                title=title,
                description=description,
                start_time=start_time_bst,
                end_time=end_time_bst
            )
        else:
            print("response error: ", response)

    def handle_task_delete(self, data, token):
        try:
            task_id = data["id"]
            appointment = GHLAppointment.objects.get(ghl_task_id=task_id)
            ghl_appointment_id = appointment.ghl_appointment_id

            headers = {
                "Authorization": f"Bearer {token.access_token}",
                "Accept": "application/json",
                "Version": "2021-04-15"
            }

            requests.delete(
                f"https://services.leadconnectorhq.com/calendars/events/{ghl_appointment_id}",
                headers=headers
            )
            appointment.delete()
        except GHLAppointment.DoesNotExist:
            pass  # Optionally log

    def get_calendar_id(self, user_id, location_id, token):
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
            "Version": "2021-04-15"
        }

        response = requests.get(
            f"https://services.leadconnectorhq.com/calendars/?locationId={location_id}",
            headers=headers
        )

        if response.status_code == 200:
            calendars = response.json().get("calendars", [])
            for cal in calendars:
                for member in cal.get("teamMembers", []):
                    if member.get("userId") == user_id:
                        return cal["id"]

        return None



class HandleUsersView(View):
    
    def get(self, request):

        token = GHLAuthCredentials.objects.first()
        pull_users(locationId=token.location_id)
        print("HH:", GHLUser.objects.all().count())

        return JsonResponse({"message": "Success"}, status=200)
    

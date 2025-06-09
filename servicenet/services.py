import requests
from core.models import GHLAuthCredentials
from servicenet.models import GHLUser

def pull_users(locationId):
    token = GHLAuthCredentials.objects.get(location_id=locationId)
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token.access_token}',
        'Content-Type': 'application/json',
        'Version': '2021-07-28'  # or '2021-04-15' for calendars endpoint
    }

    # Step 1: Fetch all calendars and map userId to calendarId
    calendar_response = requests.get(
        f"https://services.leadconnectorhq.com/calendars/?locationId={locationId}",
        headers=headers
    )

    user_calendar_map = {}
    if calendar_response.status_code == 200:
        calendars = calendar_response.json().get("calendars", [])
        for calendar in calendars:
            for member in calendar.get("teamMembers", []):
                user_id = member.get("userId")
                if user_id:
                    user_calendar_map[user_id] = calendar.get("id")
    else:
        print(f"Failed to fetch calendars: {calendar_response.status_code}")
        calendars = []

    # Step 2: Fetch users and save/update GHLUser entries
    user_response = requests.get(
        f"https://services.leadconnectorhq.com/users/?locationId={locationId}",
        headers=headers
    )

    if user_response.status_code != 200:
        print(f"Error fetching users: {user_response.status_code} - {user_response.text}")
        return

    users_data = user_response.json().get("users", [])

    for user in users_data:
        user_id = user["id"]
        GHLUser.objects.update_or_create(
            user_id=user_id,
            defaults={
                "first_name": user.get("firstName", ""),
                "last_name": user.get("lastName", ""),
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "phone": user.get("phone", ""),
                "location_id": locationId,
                "calendar_id": user_calendar_map.get(user_id)  # Map calendar if exists
            }
        )
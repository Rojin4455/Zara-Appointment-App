import requests

def get_location_data(location_id, access_token):
    url = f"https://services.leadconnectorhq.com/locations/{location_id}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Version": "2021-07-28"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("response location: ", response.json())
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None
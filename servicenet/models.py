from django.db import models

class GHLUser(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    calendar_id = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True, default="")

    def __str__(self):
        return self.name
    


class GHLAppointment(models.Model):
    ghl_appointment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    ghl_task_id = models.CharField(max_length=100, unique=True)
    contact_id = models.CharField(max_length=100)
    assigned_to = models.CharField(max_length=100)
    calendar_id = models.CharField(max_length=100)
    location_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
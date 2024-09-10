from django.db import models

# Create your models here.
class UserProfile(models.Model):
    session_id=models.CharField(max_length=100)
    FirstName = models.CharField(max_length=50,default='na')
    LastName = models.CharField(max_length=50,default='na')
    DateOfBirth = models.CharField(max_length=50,default='na')
    Email = models.EmailField(max_length=50,default='na')
    PhoneNumber = models.CharField(max_length=15,default='na')  # Adjust length based on expected format
    PreferredDateOrTime = models.CharField(max_length=50,default='na')
    state = models.CharField(max_length=50,default='start')
    locations = models.CharField(max_length=150,default='na')
    location_selected = models.CharField(max_length=150,default='na')
    providers = models.CharField(max_length=150,default='na')
    provider_selected = models.CharField(max_length=150,default='na')
    appointment_reasons = models.CharField(max_length=150,default='na')
    appointment_reason_selection = models.CharField(max_length=150,default='na')

class ChatHistory(models.Model):
    session_id = models.CharField(max_length=255)
    user_input = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
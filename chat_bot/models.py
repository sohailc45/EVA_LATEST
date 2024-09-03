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

class ChatHistory(models.Model):
    session_id = models.CharField(max_length=255)
    user_input = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)



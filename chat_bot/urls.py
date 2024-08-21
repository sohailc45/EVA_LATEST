
from django.contrib import admin
from django.urls import path,include
from. import views

urlpatterns = [
    path("", views.home, name="home"),
    path("chatbot_view", views.chatbot_view, name="chatbot_view"),
   
]

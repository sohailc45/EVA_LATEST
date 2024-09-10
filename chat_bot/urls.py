
from django.contrib import admin
from django.urls import path,include
from. import views

urlpatterns = [
    path("", views.home, name="home"),
    path("practice/<int:id>", views.home_practice, name="home"),
    path("practice2", views.home2, name="home2"),
    path("chatbot", views.home_dynamic, name="home"),
    path("chatbot_view", views.chatbot_view, name="chatbot_view"),
   
]

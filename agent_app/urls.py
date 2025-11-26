# agent_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Routes the app root to the chat UI view
    path('', views.chat_ui, name='chat_ui'), 
]
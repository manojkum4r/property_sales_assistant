# agent_app/views.py

from django.shortcuts import render

def chat_ui(request):
    """
    Renders the main chat interface HTML page.
    """
    # Renders the template from agent_app/templates/chat_frontend.html
    return render(request, 'chat_frontend.html', {})
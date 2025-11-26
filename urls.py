# property_agent_project/urls.py

from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI
from agent_app.api import router as agent_router

# Initialize Django Ninja API
api = NinjaAPI(title="Silver Land Properties AI Agent API")

# All API endpoints are registered under the router, but accessed via the /api/ prefix below
api.add_router("/", agent_router)

urlpatterns = [
    # 1. Route the server root (http://127.0.0.1:8000/) to the agent_app's URLs (which serves the UI)
    path('', include('agent_app.urls')), 
    
    # 2. Route all API endpoints to http://127.0.0.1:8000/api/
    path("api/", api.urls), 
    
    # 3. Admin remains the same
    path('admin/', admin.site.urls),
]
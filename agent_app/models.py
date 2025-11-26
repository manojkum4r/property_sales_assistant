# agent_app/models.py

from django.db import models
from django.utils import timezone
import uuid 

# --- 1. Property Model ---

class Project(models.Model):
    """Stores details about property projects available for sale."""
    
    project_name = models.CharField(max_length=255, default='Unknown Project Name') 
    no_of_bedrooms = models.IntegerField(null=True, blank=True)
    completion_status = models.CharField(max_length=50, default='available')
    bathrooms = models.IntegerField(null=True, blank=True)
    unit_type = models.CharField(max_length=100)
    developer_name = models.CharField(max_length=255)
    
    price_usd = models.DecimalField(max_digits=15, decimal_places=2)
    area_sq_mtrs = models.IntegerField()
    property_type = models.CharField(max_length=50, default='apartment') 
    
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=5, default='US')
    
    completion_date = models.DateField(null=True, blank=True)
    
    features = models.TextField(default='[]') 
    facilities = models.TextField(default='[]')
    project_description = models.TextField(default='')
    
    def __str__(self):
        return self.project_name

# --- 2. Lead Model ---

class Lead(models.Model):
    """Stores information about a prospective buyer (lead)."""
    
    # Setting null=True, blank=True is temporary to allow migration on existing rows.
    session_id = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)
    
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name or ''} ({self.session_id})"

# --- 3. Visit Booking Model ---

class VisitBooking(models.Model):
    """Tracks scheduled property viewings."""
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='pending') 
    
    def __str__(self):
        return f"Booking for {self.project.project_name} by {self.lead.session_id}"

# --- 4. Conversation Models ---

class Conversation(models.Model):
    """Represents a single chat session."""
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Conversation {self.id} with Lead {self.lead.session_id}"

class Message(models.Model):
    """Stores individual messages within a conversation."""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10) # 'Human' or 'AI'
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.sender}: {self.text[:50]}"
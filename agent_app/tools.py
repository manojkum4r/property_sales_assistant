# agent_app/tools.py

from pydantic import BaseModel, Field
from typing import List
from agent_app.models import VisitBooking, Lead
from django.db import IntegrityError
from datetime import datetime

# --- Tool Input Schemas ---

class PropertyQuery(BaseModel):
    """Input for retrieving property information from the internal database using Text-to-SQL."""
    sql_query: str = Field(description="The precise SQL query to execute against the projects table. Use JOINs and aggregate functions as needed.")

class LeadCollection(BaseModel):
    """Input for collecting final lead details and confirming a property visit booking."""
    name: str = Field(description="The user's full name.")
    email: str = Field(description="The user's email address.")
    project_name: str = Field(description="The confirmed name of the property project the user is interested in visiting.")
    city: str = Field(description="The city where the project is located.")

class WebSearchQuery(BaseModel):
    """Input for conducting a web search for external information."""
    query: str = Field(description="The query string for a web search, typically about a project feature not available in the internal database.")


# --- Tool Functions ---

# Mock function for Text-to-SQL Tool (replace with Vanna integration later)
def retrieve_property_info(query: PropertyQuery) -> str:
    """Executes a SQL query to retrieve property and project information from the database."""
    # This is a placeholder. In a real application, this function would use Vanna 
    # or another T2SQL library to safely run the query and return results.
    if "SELECT" not in query.sql_query.upper():
         return f"Error: The provided query '{query.sql_query}' is not a valid SQL SELECT statement."
         
    # Mocking a successful query response
    if "st. regis chicago" in query.sql_query.lower() and "completion" in query.sql_query.lower():
        return "The Residences at St. Regis Chicago completed on 15-10-2021."
    
    return "QUERY EXECUTED: " + query.sql_query + " | MOCK RESPONSE: Found 2 projects matching criteria: The Residences at St. Regis Chicago (2.8M USD) and Sky Tower Bangkok (1.2M USD)."


def book_property_visit(lead_details: LeadCollection) -> str:
    """Stores the collected user details and confirms a property viewing appointment."""
    try:
        # Create or update the Lead
        lead, created = Lead.objects.update_or_create(
            email=lead_details.email,
            defaults={'name': lead_details.name}
        )
        
        # Create the Booking
        VisitBooking.objects.create(
            lead=lead,
            project_name=lead_details.project_name,
            city=lead_details.city
        )
        
        return f"SUCCESS: Visit booked for {lead_details.name} for project '{lead_details.project_name}' in {lead_details.city}. A confirmation email has been sent to {lead_details.email}."
    
    except IntegrityError:
        return f"ERROR: Could not process booking due to an internal error (e.g., duplicate lead data). Please recheck the details."
    except Exception as e:
        return f"ERROR: Failed to book visit: {str(e)}"

# Mock function for Web Search Tool
def web_search(query: WebSearchQuery) -> str:
    """Performs a web search to find external information about a project."""
    # This is a placeholder for a real search tool call (e.g., Google search or Tavily)
    return f"WEB SEARCH RESULTS: For query '{query.query}': The latest real estate news suggests that the 'Sky Tower' project has recently broken ground, but local school district information is unavailable."

# The list of tools exposed to the LLM agent
TOOLS = [retrieve_property_info, book_property_visit, web_search]
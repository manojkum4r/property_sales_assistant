import os
import pandas as pd
# NOTE: Keep basic Python imports like os and pandas at the top.

# --- 1. Environment Setup (MUST COME FIRST) ---
# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'property_agent_project.settings')

# Import Django and related modules ONLY AFTER setting the environment
import django
from django.core.management import execute_from_command_line
from django.db import IntegrityError

# Call django.setup() to initialize settings
django.setup()

# Now it is safe to import your models
from agent_app.models import Project

def setup_database():
    """
    Ensures migrations are applied and loads initial project data from CSV.
    """
    
    # 1. Ensure Migrations are Applied
    try:
        print("--- 1. Running Migrations ---")
        # NOTE: We can skip running migrate here since you already ran it successfully.
        # However, keeping it makes the script robust if you delete the database again.
        # Let's ensure the database is fully ready.
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
        return

    # 2. Loading data from Property sales agent - Challenge.csv
    csv_file_path = 'Property sales agent - Challenge.csv'
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        return

    try:
        print(f"--- 2. Loading data from {csv_file_path} ---")
        
        # Clear existing data before loading
        count_before = Project.objects.count()
        Project.objects.all().delete()
        print(f"Cleared {count_before} existing Project records.")

        # Read the CSV file using pandas
        df = pd.read_csv(csv_file_path)

        # CRITICAL FIX: Convert 'completion_date' to datetime objects, coercing invalid/empty dates to NaT
        df['completion_date'] = pd.to_datetime(df['completion_date'], errors='coerce')
        
        # Rename columns to match Django model fields for clarity
        df = df.rename(columns={
            'Project name': 'project_name',
            'No of bedrooms': 'no_of_bedrooms',
            'Completion status (off plan/available)': 'completion_status',
            'bathrooms': 'bathrooms',
            'unit type': 'unit_type',
            'developer name': 'developer_name',
            'Price (USD)': 'price_usd',
            'Area (sq mtrs)': 'area_sq_mtrs',
            'Property type (apartment/villa)': 'property_type',
            'city': 'city',
            'country': 'country',
            'features': 'features',
            'facilities': 'facilities',
            'Project description': 'project_description'
        })
        
        projects_to_create = []

        for index, row in df.iterrows():
            
            # 1. Handle Date: Convert NaT (Pandas Null) to None
            completion_date_pd = row['completion_date']
            final_completion_date = None
            if pd.notna(completion_date_pd):
                final_completion_date = completion_date_pd.date() # Convert pandas Timestamp to Python date

            # 2. Handle Numerics: Convert NaN/None (for nullable fields) to None
            # This is safer than using or None for pandas NaN/NaT values
            no_of_bedrooms = row.get('no_of_bedrooms')
            if pd.isna(no_of_bedrooms):
                no_of_bedrooms = None
            
            bathrooms = row.get('bathrooms')
            if pd.isna(bathrooms):
                bathrooms = None
                
            area_sq_mtrs = row.get('area_sq_mtrs')
            if pd.isna(area_sq_mtrs):
                area_sq_mtrs = None
            
            # 3. Create Project Object
            project = Project(
                project_name=row['project_name'],
                no_of_bedrooms=no_of_bedrooms, 
                completion_status=row['completion_status'],
                bathrooms=bathrooms,
                unit_type=row['unit_type'],
                developer_name=row['developer_name'],
                price_usd=row['price_usd'],
                area_sq_mtrs=area_sq_mtrs,
                property_type=row['property_type'],
                city=row['city'],
                country=row['country'],
                completion_date=final_completion_date, 
                features=row['features'],
                facilities=row['facilities'],
                project_description=row['project_description']
            )
            projects_to_create.append(project)

        # Use bulk_create for performance
        Project.objects.bulk_create(projects_to_create)

        print(f"Loaded {Project.objects.count()} new Project records.")

    except Exception as e:
        print(f"An error occurred during data loading: {e}")


if __name__ == "__main__":
    # Ensure pandas is available, as it is critical for this script
    try:
        import pandas as pd 
    except ImportError:
        print("Error: pandas is not installed. Please run: pip install pandas")
        exit(1)
        
    setup_database()
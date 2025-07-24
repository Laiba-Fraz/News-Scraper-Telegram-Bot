import os
from dotenv import load_dotenv
from supabase import create_client

# Load the .env file, with path correction
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))  # Go one directory up to find the .env file

# Fetch environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

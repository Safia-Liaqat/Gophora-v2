import os
from dotenv import load_dotenv

# load_dotenv() is ONLY for local development testing
load_dotenv() 

# Access the secret key injected by Firebase Secret Manager
JWT_SECRET = os.environ.get('JWT_SECRET')
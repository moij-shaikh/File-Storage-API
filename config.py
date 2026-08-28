import os
from dotenv import load_dotenv
load_dotenv()

jwt_key=os.getenv("JWT_SECRET_KEY")
jwt_algoritm=os.getenv("JWT_ALGORITHM")

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY=os.getenv("SUPABASE_SECRET_KEY")

sender=os.getenv("Email_name")
email_pass=os.getenv("Email_pass")

secret_key=os.getenv("SESSION_SECRET_KEY")
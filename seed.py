import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from faker import Faker

# Important: We need to be able to import things from your other files.
# To make sure Python can find your app.py (for User, Task models) and
# user_registration.py (for pwd_context), we might need to adjust the Python path
# if seed.py is in the root and those files are in a subdirectory.
# For now, let's assume they are accessible or we'll adjust if needed.
from app import User, Task, Base # Assuming User, Task, Base are in app.py
from user_registration import pwd_context # Assuming pwd_context is in user_registration.py

# Load environment variables (especially DATABASE_URL and JWT_KEY)
# If you have a .env file, make sure it's loaded.
# If apiUtil.py already calls load_dotenv(), and you import something from it,
# that might be enough. Otherwise, call it here:
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Faker
fake = Faker()

# This is crucial if your main app's Base.metadata.create_all(engine)
# might not have run yet in the context of this script, or if you're running
# this script against an empty database for the first time.
# It ensures tables exist before we try to insert data.
Base.metadata.create_all(bind=engine)

print("Database connection and Faker initialized.")
print("Next steps: Write functions to seed users and tasks.")

# We will add our seeding functions here later
import os
import random
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, scoped_session
from faker import Faker



from app import User, Task, Base 
from user_registration import pwd_context


from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Faker
fake = Faker()

Base.metadata.create_all(bind=engine)

print("Database connection and Faker initialized.")
print("Next steps: Write functions to seed users and tasks.")

def seed_users(db_session, num_users):
    print(f"Seeding {num_users} users...")
    users_created_count = 0
    for i in range(num_users):
        fake_username = f'{fake.user_name()}__{i}'
        fake_password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        
        hashed_password = pwd_context.hash(fake_password)

        new_user = User(username=fake_username, hashed_password=hashed_password)

        db_session.add(new_user)
        users_created_count += 1

        try:
            db_session.commit()
            print(f'Successfully seeded {users_created_count} users.')
        except Exception as e:
            db_session.rollback()
            print(f'Error seeding users: {e}')

def seed_tasks(db_session, num_tasks_per_user_avg):
    users = db_session.scalars(select(User)).all()
    if not users:
        print("No users found in the database. Please seed users first.")
        return
    
    print(f'Attempting to seed tasks for {len(users)} users (avg ~{num_tasks_per_user_avg} tasks per user)...')
    total_tasks_created = 0

    for user_obj in users:
        num_individual_tasks = random.randint(1, max(1,(num_tasks_per_user_avg * 2) -1))

    for i in range(num_individual_tasks):
        task_description = fake.sentence(nb_words=random.randint(4,8))
        task_completed = fake.boolean(chance_of_getting_true=25)
        task_due_date = fake.future_date(end_date="+60d").strftime('%Y-%m-%d')
        task_location = fake.city() if fake.boolean(chance_of_getting_true=60) else None

        new_task = Task(
            description=task_description,
            completed=task_completed,
            due_date=task_due_date,
            location=task_location,
            owner_id=user_obj.id
        )
        db_session.add(new_task)
        total_tasks_created += 1

        try:
            db_session.commit()
            print(f'Successfully seeded {total_tasks_created} tasks across {len(users)} users.')
        except Exception as e:
            db_session.rollback()
            print(f'Error seeding tasks: {e}')

if __name__ == "__main__":
    db = SessionLocal()
    try:

        #Clear existing table data before seeding
        print(f'Clearing existing table data...')
        num_tasks_deleted = db.query(Task).delete()
        num_users_deleted = db.query(User).delete()
        print(f'{num_users_deleted} users deleted from table.')
        print(f'{num_tasks_deleted} tasks deleted from table.')

        # Seed a specific number of users
        #seed_users(db, 50)
        seed_users(db, 10)
        seed_tasks(db, 5)

    finally:
        print("Closing database session.")
        db.close()

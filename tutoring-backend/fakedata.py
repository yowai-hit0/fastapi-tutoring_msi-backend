from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker
import random
from datetime import datetime, timedelta

from main import User, Tutor, Student, TutoringSession  # Import your models

# Database setup (use your actual database URL)
DATABASE_URL = "postgresql://postgres:gomgom1029@localhost:5432/tutoring_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Create a Faker instance
fake = Faker()


# Helper function to create users
def create_user():
    username = fake.user_name()
    email = fake.email()
    hashed_password = fake.password(length=12)
    user = User(username=username, email=email, hashed_password=hashed_password)

    return user


# Helper function to create tutors
def create_tutor(user_id):
    bio = fake.text(max_nb_chars=500)
    tutor = Tutor(user_id=user_id, bio=bio)
    return tutor


# Helper function to create students
def create_student(tutor_id):
    name = fake.name()
    email = fake.email()
    age = random.randint(18, 50)
    student = Student(tutor_id=tutor_id, name=name, email=email, age=age)
    return student


# Helper function to create tutoring sessions
def create_tutoring_session(tutor_id, student_id):
    date = fake.date_this_year(before_today=True, after_today=False)
    duration = random.randint(30, 120)  # Session length in minutes
    topic = fake.bs()  # Fake business-related topic
    session = TutoringSession(tutor_id=tutor_id, student_id=student_id, date=date, duration=duration, topic=topic)
    return session


# Insert data into the database
def insert_data():
    users = []
    tutors = []
    students = []
    sessions = []

    for _ in range(500000):
        # Create a user and add to list
        user = create_user()
        users.append(user)

        if len(users) >= 1000:
            db.bulk_save_objects(users)
            db.commit()
            users = []

        # Create tutor linked to the user
        tutor = create_tutor(user.id)
        tutors.append(tutor)

        if len(tutors) >= 1000:
            db.bulk_save_objects(tutors)
            db.commit()
            tutors = []
            print("done tutor ")

        # Create student linked to the tutor
        student = create_student(tutor.id)
        students.append(student)

        if len(students) >= 1000:
            db.bulk_save_objects(students)
            db.commit()
            students = []
            print("done students ")
        # Create tutoring session for this tutor and student
        session = create_tutoring_session(tutor.id, student.student_id)
        sessions.append(session)

        if len(sessions) >= 1000:
            db.bulk_save_objects(sessions)
            db.commit()
            sessions = []
            print("done session ")


    # Commit any remaining records
    if users:
        db.bulk_save_objects(users)
        db.commit()


    if tutors:
        db.bulk_save_objects(tutors)
        db.commit()

    if students:
        db.bulk_save_objects(students)
        db.commit()

    if sessions:
        db.bulk_save_objects(sessions)
        db.commit()


insert_data()
print("Data generation and insertion completed.")

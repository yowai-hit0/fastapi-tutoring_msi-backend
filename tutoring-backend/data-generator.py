import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import User, Tutor, Student, TutoringSession
import faker

# Set up the database connection
DATABASE_URL = "postgresql://postgres:gomgom1029@localhost:5432/tutoring_db"  # Replace with your actual database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a session
db = SessionLocal()

# Create Faker instance for generating fake data
fake = faker.Faker()



# Function to add a user
def add_user(username: str, email: str, password: str, bio: str):
    user = User(username=username, email=email)
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)

    new_tutor = Tutor(user_id=user.id, bio=bio)
    db.add(new_tutor)
    db.commit()
    return user, new_tutor
# Function to add a student
def add_student(tutor_id: int, name: str, email: str, age: int):
    student = Student(tutor_id=tutor_id, name=name, email=email, age=age)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

# Function to add a tutoring session
def add_tutoring_session(tutor_id: int, student_id: int, date: datetime, duration: int, topic: str):
    session = TutoringSession(tutor_id=tutor_id, student_id=student_id, date=date, duration=duration, topic=topic)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

# Function to generate random data
def generate_large_dummy_data(num_users=1000, num_students=5000, num_sessions=2000):
    # Generate Users and Tutors
    for _ in range(num_users):
        username = fake.user_name()
        email = fake.email()
        password = fake.password()
        bio = fake.text(max_nb_chars=200)
        user, tutor = add_user(username, email, password, bio)
    # Generate Students
    for _ in range(num_students):
        tutor_id = random.choice([tutor.id for tutor in db.query(Tutor).all()])
        name = fake.name()
        email = fake.email()
        age = random.randint(18, 40)
        add_student(tutor_id, name, email, age)

    # Generate Tutoring Sessions
    for _ in range(num_sessions):
        tutor_id = random.choice([tutor.id for tutor in db.query(Tutor).all()])
        student_id = random.choice([student.student_id for student in db.query(Student).all()])
        date = fake.date_this_year(before_today=True, after_today=False)
        date = datetime.combine(date, datetime.min.time())
        duration = random.randint(30, 120)  # Duration in minutes
        topic = fake.word() + " " + fake.word()  # Random topic
        add_tutoring_session(tutor_id, student_id, date, duration, topic)

    print(f"Added {num_users} users, {num_users} tutors, {num_students} students, and {num_sessions} tutoring sessions.")

# Example of adding large amounts of data
generate_large_dummy_data(num_users=20000, num_students=500000, num_sessions=500000)
db.close()

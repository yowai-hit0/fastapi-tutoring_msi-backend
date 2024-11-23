from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

# Base class for SQLAlchemy models
Base = declarative_base()

# Password hashing utility using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PostgreSQL database URL (replace with your actual details)
DATABASE_URL = "postgresql://postgres:gomgom1029@localhost:5432/tutoring_db"

# Create the database engine
engine = create_engine(DATABASE_URL)


# Create the SessionLocal session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String)

    tutor = relationship("Tutor", uselist=False, back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verify the user's password."""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.hashed_password = pwd_context.hash(password)


class Tutor(Base):
    __tablename__ = 'tutors'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    bio = Column(Text, nullable=True)

    user = relationship("User", back_populates="tutor")
    students = relationship("Student", back_populates="tutor")
    sessions = relationship("Session", back_populates="tutor")


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey('tutors.id'))
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    age = Column(Integer, nullable=True)

    tutor = relationship("Tutor", back_populates="students")
    sessions = relationship("Session", back_populates="student")


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey('tutors.id'))  # Foreign key to the Tutor table
    student_id = Column(Integer, ForeignKey('students.id'))  # Foreign key to the Student table
    date = Column(String)  # Consider changing this to a Date or DateTime type if needed
    duration = Column(Integer)  # Duration in minutes
    topic = Column(String(200))  # Added length for topic

    tutor = relationship("Tutor", back_populates="sessions")
    student = relationship("Student", back_populates="sessions")


# Create the tables in the database (only once, then comment it out if not needed)
Base.metadata.create_all(bind=engine)

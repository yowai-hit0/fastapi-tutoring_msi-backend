from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

# Base class for SQLAlchemy models
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str) -> None:
        self.hashed_password = pwd_context.hash(password)


class Tutor(Base):
    __tablename__ = 'tutors'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    bio = Column(Text, nullable=True)
    user = relationship("User", back_populates="tutor")
    students = relationship("Student", back_populates="tutor")
    sessions = relationship("TutoringSession", back_populates="tutor")


class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey('tutors.id'))
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    age = Column(Integer, nullable=True)
    tutor = relationship("Tutor", back_populates="students")
    sessions = relationship("TutoringSession", back_populates="student")


class TutoringSession(Base):
    __tablename__ = 'tutoring_sessions'
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey('tutors.id'))
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(DateTime)
    duration = Column(Integer)
    topic = Column(String(200))
    tutor = relationship("Tutor", back_populates="sessions")
    student = relationship("Student", back_populates="sessions")


Base.metadata.create_all(bind=engine)
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String)

    tutor = relationship("Tutor", uselist=False, back_populates="user")





Base.metadata.create_all(bind=engine)

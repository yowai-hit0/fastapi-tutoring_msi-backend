from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext
from typing import List


Base = declarative_base()
DATABASE_URL = "postgresql://postgres:gomgom1029@localhost:5432/tutoring_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=False, index=True)
    email = Column(String(100), unique=False, index=True)
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
    student_id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey('tutors.id'))
    name = Column(String(100))
    email = Column(String(100), unique=False, index=True)
    age = Column(Integer, nullable=True)
    tutor = relationship("Tutor", back_populates="students")
    sessions = relationship("TutoringSession", back_populates="student")


class TutoringSession(Base):
    __tablename__ = 'tutoring_sessions'
    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey('tutors.id'))
    student_id = Column(Integer, ForeignKey('students.student_id'))
    date = Column(DateTime)
    duration = Column(Integer)
    topic = Column(String(200))
    tutor = relationship("Tutor", back_populates="sessions")
    student = relationship("Student", back_populates="sessions")


Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    age: int | None = None

class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int | None

    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    student_id: int
    date: datetime
    duration: int
    topic: str

class SessionResponse(BaseModel):
    id: int
    tutor_id: int
    student_id: int
    date: datetime
    duration: int
    topic: str

    class Config:
        orm_mode = True


# Auth apis
@app.post("/register/")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already taken",
        )
    new_user = User(username=user.username, email=user.email)
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_tutor = Tutor(user_id=new_user.id)
    db.add(new_tutor)
    db.commit()
    return {"msg": "User registered successfully", "user_id": new_user.id}

@app.post("/token/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# CRUD for Students and Sessions
@app.post("/students/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for the current user"
        )
    new_student = Student(
        name=student.name,
        email=student.email,
        age=student.age,
        tutor_id=tutor.id
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


@app.get("/students/", response_model=List[StudentResponse])
def get_students(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for the current user"
        )
    return tutor.students


@app.get("/students/unprotected/", response_model=List[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    students = db.query(Student)
    if not students:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for the current user"
        )
    return students
@app.get("/sessions/unprotected", response_model=List[SessionResponse])
def get_sessions(db: Session = Depends(get_db)):
    my_session = db.query(TutoringSession)
    if not my_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for the current user"
        )
    return my_session

@app.put("/students/{student_id}/", response_model=StudentResponse)
def update_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_student = db.query(Student).filter(Student.id == student_id).first()
    if not existing_student or existing_student.tutor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or unauthorized to update"
        )
    existing_student.name = student.name
    existing_student.email = student.email
    existing_student.age = student.age
    db.commit()
    db.refresh(existing_student)
    return existing_student


@app.delete("/students/{student_id}/")
def delete_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_student = db.query(Student).filter(Student.id == student_id).first()
    if not existing_student or existing_student.tutor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or unauthorized to delete"
        )
    db.delete(existing_student)
    db.commit()
    return {"msg": "Student deleted successfully"}


@app.post("/sessions/", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for the current user"
        )
    student = db.query(Student).filter(Student.id == session.student_id, Student.tutor_id == tutor.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or not assigned to the current tutor"
        )
    new_session = TutoringSession(
        tutor_id=tutor.id,
        student_id=student.id,
        date=session.date,
        duration=session.duration,
        topic=session.topic
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@app.get("/sessions/", response_model=List[SessionResponse])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for the current user"
        )
    return tutor.sessions




@app.put("/sessions/{session_id}/", response_model=SessionResponse)
def update_session(session_id: int, session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_session = db.query(TutoringSession).filter(TutoringSession.id == session_id).first()
    if not existing_session or existing_session.tutor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or unauthorized to update"
        )
    student = db.query(Student).filter(Student.id == session.student_id, Student.tutor_id == existing_session.tutor_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or not assigned to the current tutor"
        )
    existing_session.student_id = student.id
    existing_session.date = session.date
    existing_session.duration = session.duration
    existing_session.topic = session.topic
    db.commit()
    db.refresh(existing_session)
    return existing_session


@app.delete("/sessions/{session_id}/")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_session = db.query(TutoringSession).filter(TutoringSession.id == session_id).first()
    if not existing_session or existing_session.tutor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or unauthorized to delete"
        )
    db.delete(existing_session)
    db.commit()
    return {"msg": "Session deleted successfully"}
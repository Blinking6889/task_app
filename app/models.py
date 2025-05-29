from sqlalchemy import Column,create_engine,Integer,String,Select,Boolean, ForeignKey
from sqlalchemy.orm import declarative_base,sessionmaker,scoped_session, relationship

#Define Database Structure
Base = declarative_base()
class Task(Base):
    __tablename__ = "task_data"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    completed = Column(Boolean)
    due_date = Column(String)
    location = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)
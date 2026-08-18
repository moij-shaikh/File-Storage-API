from sqlalchemy import create_engine , ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,DeclarativeBase,sessionmaker
import os 
from dotenv import load_dotenv
load_dotenv()
import logging

engine=create_engine(os.getenv("DATABASE_URL"))
make_session=sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass
class User(Base):
    __tablename__="users"
    full_name:Mapped[str]
    username:Mapped[str]=mapped_column(primary_key=True)
    password:Mapped[str]
    email:Mapped[str]
    is_verified:Mapped[bool]

class UserFile(Base):
    __tablename__="files"
    id:Mapped[int]=mapped_column(primary_key=True)
    original_file_name:Mapped[str]=mapped_column(nullable=False)
    stored_file_name:Mapped[str]
    file_type:Mapped[str]
    username:Mapped[str]=mapped_column(ForeignKey("users.username",ondelete="CASCADE"))

Base.metadata.create_all(engine)
logging.info("DataBase Tables was created successfully.")

def get_db():
    try:
        db=make_session()
        yield db
    finally:
        db.close()
        
        

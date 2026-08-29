from sqlalchemy import  ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine , async_sessionmaker

from config import DATABASE_URL

engine=create_async_engine(DATABASE_URL)
make_session=async_sessionmaker(bind=engine,expire_on_commit=False)

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
class Admin(Base):
    __tablename__="admin"
    username:Mapped[str]=mapped_column(primary_key=True)
    password:Mapped[str]
    email:Mapped[str]

async def get_db():
    async with make_session() as db:
        yield db
    
        
        

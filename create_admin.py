from database import Admin , make_session
from utils import pass_hasher
from sqlalchemy import select
import asyncio
async def create_admin():
    username=input("Enter admin username")
    password=input("Enter admin password")
    email=input("Enter admin email")

    async with make_session() as s:
        exists= await s.scalar(select(Admin))
        if exists:
            print("Admin is already present, Delete from db to create new.")
        admin=Admin(username=username,password=pass_hasher.hash(password),email=email)   
        s.add(admin)
        await s.commit()
        print("Admin Created")

if __name__=="__main__":
    asyncio.run(create_admin())
from fastapi import APIRouter ,Depends,Request ,HTTPException , status,Response , BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import secrets 
from utils import pass_hasher ,supabase,send_email_to_verify
from auth import make_jwt_access_token , get_current_verified_user , make_jwt_refresh_token , check_generate_refresh_token
from schemas import Register_user
from storage3.utils import StorageException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from database import get_db,User

import logging

router=APIRouter(prefix="/user")

@router.post("",tags=["User"],description="Here user can register")
async def Register_user(bg_task:BackgroundTasks,req:Request,Data:Register_user,db:AsyncSession=Depends(get_db)):
    existing= await db.scalar(select(User).where(User.email==Data.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="email already exist ")
    existing=await db.scalar(select(User).where(User.username==Data.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already exist ")
    user=User(full_name=Data.full_name,username=Data.username,email=Data.email,is_verified=False,password=pass_hasher.hash(Data.password))
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        token=secrets.token_urlsafe(32)
        await req.app.state.redis.set(f"email_verify_token:{token}",Data.username,ex=60*5)
        url=f"http://127.0.0.1:8000/user/verify_email?token={token}"
        bg_task.add_task(send_email_to_verify,Data.email,url)
        logging.info("%s was successfully registered and email for verification is Sended ",user.username)    
        return f"Successfully Registered ,Check Email for  Verification {token}"
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down try again later.")

@router.delete("",tags=["User"])
async def delete_user(res:Response,req:Request,user:str=Depends(get_current_verified_user),db:AsyncSession=Depends(get_db)):
    db_user= await db.get(User,user)
    if db_user is None:
        raise HTTPException(detail="Something Went Wrong try again",status_code=status.HTTP_404_NOT_FOUND)
    storage=supabase.storage.from_("drive")
    files=storage.list(user)
    try:
        for file in files:
            storage.remove([f"{user}/{file['name']}"])
        await db.delete(db_user)
        await db.commit()
        token=req.cookies.get("refresh_token")
        await req.app.state.redis.delete(f"refresh_token:{token}")
        res.delete_cookie("refresh_token")
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Not Responding")
    except StorageException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Server is Not Responding")

@router.get("/verify_email",tags=["Auth"])
async def verify_email(req:Request,token:str,db:AsyncSession=Depends(get_db)):
    redis_token = await req.app.state.redis.get(f"email_verify_token:{token}")
    if redis_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="email not verified ")
    try:
        user= await db.get(User,redis_token)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found ")
        user.is_verified=True
        await db.commit()
        await req.app.state.redis.delete(f"email_verify_token:{token}")
        logging.info("%s : Email was verified. ",user.username)
        return "Successfully Verified"
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down try again later.")

@router.post("/login",tags=["User"])
async def user_login(req:Request,res:Response,form_data:OAuth2PasswordRequestForm=Depends(),db:AsyncSession=Depends(get_db)):
    username = form_data.username
    password = form_data.password
    user=await db.get(User,username)
    if user is None:
        logging.info("unknown username attempted login: %s",username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found ")
    if not user.is_verified:
        logging.warning("%s was trying to login but its email is not verified ",user.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Verify Email  ")
    is_same=pass_hasher.verify(password,user.password)
    if not is_same:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Password is not correct")
    token=make_jwt_access_token(user.username)
    refresh_token=make_jwt_refresh_token(user.username)
    res.set_cookie(key="refresh_token",value=refresh_token,samesite="strict",httponly=True,max_age=60*60*24*10,path="/user")
    await req.app.state.redis.set(f"refresh_token:{refresh_token}",user.username,ex=60*60*24*10)
    logging.info("%s was successfully login",username)
    return {
        "token_type":"bearer",
        "access_token":token
    }

@router.post("/auth/refresh",tags=["Auth"])
async def handle_refresh_token(req:Request,token:str=Depends(check_generate_refresh_token)):
    return {
        "token_type":'bearer',
        "access_token":token
    }
 
@router.post("/logout",tags=["User"])
async def logout_user(res:Response,req:Request,user:str=Depends(get_current_verified_user)):
    refresh_token=req.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    redis_token=await req.app.state.redis.get(f"refresh_token:{refresh_token}")
    if redis_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user Already Logout")
    await req.app.state.redis.delete(f"refresh_token:{refresh_token}")
    res.delete_cookie("refresh_token",path="/user")
    logging.info("%s was logout successfully",user)
    return {
        "message":"Logout"
    }

from fastapi import APIRouter ,Depends,Request ,HTTPException , status,Response,BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from jose import jwt 
from jose.exceptions import JWTError
import secrets 
from utils import pass_hasher , redis,supabase,send_email_to_verify,get_current_verified_user
from schemas import Register_user
from storage3.utils import StorageException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from database import get_db,User

from dotenv import load_dotenv
import os
import logging
from datetime import timedelta , timezone,datetime

load_dotenv()

router=APIRouter(prefix="/user")
jwt_key=os.getenv("JWT_SECRET_KEY")
jwt_algoritm=os.getenv("JWT_ALGORITHM")

@router.post("",tags=["User"],description="Here user can register")
def Register_user(Data:Register_user,db:Session=Depends(get_db)):
    user=User(full_name=Data.full_name,username=Data.username,email=Data.email,is_verified=False,password=pass_hasher.hash(Data.password))
    existing=db.scalar(select(User).where(User.email==Data.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="email already exist ")
    existing=db.scalar(select(User).where(User.username==Data.username))
    if existing:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already exist ")
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        token=secrets.token_urlsafe(32)
        redis.set(f"email_verify_token:{token}",Data.username,ex=60*5)
        url=f"http://127.0.0.1:8000/user/verify_email?token={token}"
        logging.info("%s was register",user.username)
        # bg_task.add_task(send_email_to_verify,Data.email,url)
        logging.info("%s was successfully registered and email for verification is Sended ",user.username)    
        return "Successfully Registered ,Check Email for  Verification "
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down try again later.")


@router.get("/verify_email",tags=["Auth"])
def verify_email(token:str,db:Session=Depends(get_db)):
    redis_token=redis.get(f"email_verify_token:{token}")
    if redis_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="email not verified ")
    else:
        user=db.get(User,redis_token)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found ")
        user.is_verified=True
        db.commit()
        redis.delete(f"email_verify_token:{token}")
        logging.info("%s : Email was verified. ",user.username)
        return "Successfully Verified"

@router.post("/login",tags=["User"])
def user_login(res:Response,form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    username = form_data.username
    password = form_data.password
    user=db.get(User,username)
    if user is None:
        logging.info("unknown username attempted login: %s",username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found ")
    if not user.is_verified:
        logging.warning("%s was trying to login but its email is not verified ",user.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Verify Email  ")
    
    hashed_pass=user.password
    is_same=pass_hasher.verify(password,hashed_pass)
    if not is_same:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Password is not correct")
    if is_same:
        payload={
            "sub":str(user.username),
            "exp":datetime.now(timezone.utc)+timedelta(minutes=15)
        }
        payload2={
                    "sub":str(user.username),
                    "exp":datetime.now(timezone.utc)+timedelta(days=7)
                }
        access_token=jwt.encode(payload,jwt_key,algorithm=jwt_algoritm)
        refresh_token=jwt.encode(payload2,jwt_key,algorithm=jwt_algoritm)
        redis_token=f"refresh_token:{refresh_token}"
        redis.set(redis_token,user.username,ex=timedelta(days=7))
        res.set_cookie(key="refresh",value=refresh_token,httponly=True,samesite="lax",path="/user/refresh")
        logging.info("%s was successfully login",username)
        return {
            "token_type":"bearer",
            "access_token": access_token,
        }
        
        
@router.post("/refresh",tags=["Auth"])
def handle_refresh_token(req:Request):
    token=req.cookies.get("refresh")
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Login In")
    redis_token=redis.get(f"refresh_token:{token}")
    if redis_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login Fails")
    payload={
        "sub":str(redis_token),
        'exp':datetime.now(timezone.utc)+timedelta(minutes=10)
    }
    new_token=jwt.encode(payload,jwt_key,algorithm=jwt_algoritm)
    return {
        "token_type":'bearer',
        "access_token":new_token
    }
    
    


    
@router.post("/logout",tags=["User"])
def logout_user(res:Response,req:Request,user:str=Depends(get_current_verified_user)):
    refresh_token=req.cookies.get("refresh")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    redis_token=redis.get(f"refresh_token:{refresh_token}")
    if redis_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user Already Logout")
    redis.delete(f"refresh_token:{refresh_token}")
    res.delete_cookie("refresh")
    logging.info("%s was logout successfully",user)
    return 

@router.delete("/delete",tags=["User"])
def delete_user(res:Response,req:Request,user:str=Depends(get_current_verified_user),db:Session=Depends(get_db)):
    db_user=db.get(User,user)
    if db_user is None:
        raise HTTPException(detail="Something Went Wrong try again",status_code=status.HTTP_404_NOT_FOUND)
    storage=supabase.storage.from_("drive")
    files=storage.list(user)
    try:
        for i in files:
            storage.remove([f"{user}/{i}"])
        db.delete(db_user)
        db.commit()
        token=req.cookies.get("refresh")
        redis.delete(f"refresh_token:{token}")
        res.delete_cookie("refresh")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Not Responding")
    except StorageException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Server is Not Responding")

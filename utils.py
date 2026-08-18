import os
from dotenv import load_dotenv
load_dotenv()
from pwdlib import PasswordHash
import redis
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException,status
from jose import jwt , JWTError
jwt_key=os.getenv("JWT_SECRET_KEY")
jwt_algoritm=os.getenv("JWT_ALGORITHM")

get_jwt_token=OAuth2PasswordBearer(tokenUrl="/user/login")
pass_hasher=PasswordHash.recommended()

def get_current_verified_user(token:str=Depends(get_jwt_token)):
    try:
        payload=jwt.decode(token,jwt_key,algorithms=[jwt_algoritm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login First")
    user=payload.get("sub")
    return user

redis=redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True        
    )

import smtplib
sender=os.getenv("Email_name")
email_pass=os.getenv("Email_pass")
from email.message import EmailMessage
def send_email_to_verify(email,url):
    msg=EmailMessage()
    msg["From"]=sender
    msg["TO"]=email
    msg["Subject"]="Verify Email"
    msg.set_content(f"""
    <a href={url}>Click to verify</a>
""")
    smtp=smtplib.SMTP_SSL("smtp.gmail.com",465)
    smtp.login(sender,email_pass)
    smtp.send_message(msg)
    return "Sended"


import clamd
scanner=clamd.ClamdUnixSocket("/run/clamav/clamd.ctl")
    

import supabase
SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY=os.getenv("SUPABASE_SECRET_KEY")
supabase=supabase.create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
    
)
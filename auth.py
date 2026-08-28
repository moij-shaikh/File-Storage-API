from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException,status
from jose import jwt , JWTError
from config import jwt_algoritm , jwt_key
from datetime import datetime , timezone, timedelta

get_jwt_token=OAuth2PasswordBearer(tokenUrl="/user/login")

def get_current_verified_user(token:str=Depends(get_jwt_token)):
    try:
        payload=jwt.decode(token,jwt_key,algorithms=[jwt_algoritm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login First")
    user=payload.get("sub")
    return user

def make_jwt_access_token(sub)->str:
    payload={
        "sub":str(sub),
        'exp':datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    token= jwt.encode(payload,jwt_key,algorithm=jwt_algoritm)
    return  token

def make_jwt_refresh_token(sub)->str:
    payload={
        "sub":str(sub),
        'exp':datetime.now(timezone.utc) + timedelta(days=10)
    }
    token= jwt.encode(payload,jwt_key,algorithm=jwt_algoritm)
    return  token
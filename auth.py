from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException,status
from jose import jwt , JWTError
from config import jwt_algoritm , jwt_key


get_jwt_token=OAuth2PasswordBearer(tokenUrl="/user/login")

def get_current_verified_user(token:str=Depends(get_jwt_token)):
    try:
        payload=jwt.decode(token,jwt_key,algorithms=[jwt_algoritm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Login First")
    user=payload.get("sub")
    return user
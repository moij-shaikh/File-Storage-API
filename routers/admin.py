from fastapi import APIRouter , Depends , Request , Response , HTTPException , status
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db,Admin
from sqlalchemy.ext.asyncio import AsyncSession 
from utils import supabase , pass_hasher
from auth import make_jwt_access_token , make_jwt_refresh_token ,check_admin

router=APIRouter(prefix="/admin")

@router.post("/login",tags=["Admin"])
async def admin__login(res:Response,req:Request,form_data:OAuth2PasswordRequestForm=Depends(),db:AsyncSession=Depends(get_db)):
    admin=await db.get(Admin,form_data.username)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Admin Found")

    if not pass_hasher.verify(form_data.password,admin.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Try again later")
    access_token=make_jwt_access_token(sub=admin.username,role="admin")
    refresh_token=make_jwt_refresh_token(sub=admin.username,role="admin")
    res.set_cookie(key="admin_refresh_token",value=refresh_token,samesite="strict",httponly=True,path="/admin",max_age=60*60*24*10)
    await req.app.state.redis.set(f"admin_refresh_token:{refresh_token}","1",ex=60*60*24*10)
    return {
        "token_type":"bearer",
        "access_token":access_token
    }
@router.post("/logout",tags=["Admin"])
async def admin__logout(res:Response,req:Request,admin:str=Depends(check_admin)):
    refresh_token=req.cookies.get("admin_refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Login First.")
    redis_token= await req.app.state.redis.get(f"admin_refresh_token:{refresh_token}")
    if redis_token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Login First.")
    res.delete_cookie("admin_refresh_token")
    await req.app.state.redis.delete(f"admin_refresh_token:{refresh_token}")
 
    return{
        "message":"Logout Successfully"
    }

@router.get("/folder",tags=["Admin Folder"])
def admin__show_folders(admin:str=Depends(check_admin)):
    storage=supabase.storage.from_("drive")
    folders=storage.list()
    display=[folder.get("name") for folder in folders]
    return display

@router.get("/folder/{name}",tags=["Admin Folder"])
def admin__show_file(name:str,admin:str=Depends(check_admin)):
    storage=supabase.storage.from_("drive")
    folder=storage.list(name)
    if not folder or folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Folder Found.")
    display=[
        {
            "id":file.get("id"),
            "name":file.get("name"),
            "uploaded_at":file.get("created_at"),
            "last_accessed_at":file.get("last_accessed_at"),
            "size":f"{round(file.get("metadata").get("size") / (1024*1024),2)} MB"
        }
        for file in folder
    ]
    return display

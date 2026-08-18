from fastapi import APIRouter,Response,Depends,HTTPException,File,UploadFile,Query
from fastapi import status
from database import get_db,UserFile,User
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from storage3.utils import StorageException
from utils import scanner ,supabase ,get_current_verified_user
from schemas import Rename_file
import uuid
import os
from dotenv import load_dotenv
load_dotenv()
jwt_key=os.getenv("JWT_SECRET_KEY")
jwt_algoritm=os.getenv("JWT_ALGORITHM")

router=APIRouter(prefix="/file")
@router.post("/upload",tags=["files"],description="This Routes is used to upload Files.")
def upload_file(db:Session=Depends(get_db),user:str=Depends(get_current_verified_user),user_file:UploadFile=File(title="Choose file")):
    file_type=user_file.content_type
    allowed_files=["application/pdf","image/png","image/jpg","image/jpeg"]
    if file_type not in allowed_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Image not supported") 
    scan_result=scanner.instream(user_file.file)
    if scan_result.get('stream')[0] !="OK":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Found virus ")
    user_file.file.seek(0)
    file=user_file.file.read()
    storage=supabase.storage.from_("drive")
    file_name=uuid.uuid4()
    original_file_name=user_file.filename
    try:
        storage.upload(
                    path=f"{user}/{file_name}",
                    file=file
                )
        db_file=UserFile(original_file_name=original_file_name,stored_file_name=file_name,username=user,file_type=file_type)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    except SQLAlchemyError :
        db.rollback()
        file=f"{user}/{file_name}"
        storage.remove([file])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Something went wrong, Check File name")
    except StorageException:
        raise HTTPException(detail="Something went wrong",status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return {"ID":db_file.id,"Name":original_file_name}

@router.get("/uploaded",tags=["files"],description="This Routes is used to View All uploaded Files.")
def show_uploaded_file(db:Session=Depends(get_db),payload_user:str=Depends(get_current_verified_user)):
    try:
        db_files=db.execute(select(UserFile.original_file_name).where(UserFile.username==payload_user)).scalars().all()
        if not db_files:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No files Found")           
        return db_files
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Something went wrong")

@router.patch("/rename",tags=["files"],description="This Routes is used to Rename uploaded Files.")
def rename_uploaded_file(Data:Rename_file,user:str=Depends(get_current_verified_user),db:Session=Depends(get_db)):
    try:
        db_file=db.get(UserFile,Data.id)
        if db_file is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File Not Found")
        if user == db_file.username:
            db_file.original_file_name=Data.name
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File Not Found")
        return "File Name Updated Successfully "
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not Responding")
    
@router.delete("/uploaded",tags=["files"],description="This Routes is used to Delete uploaded Files.")
def delete_uploaded_file(id:int=Query(...),user:str=Depends(get_current_verified_user),db:Session=Depends(get_db)):  
    try:
        db_file=db.get(UserFile,id)
        if not db_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
        drive=supabase.storage.from_("drive")
        if db_file.username==user:
            file_name=db_file.original_file_name
            stored_file=db_file.stored_file_name
            db.delete(db_file)
            drive.remove([f"{user}/{stored_file}"])
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File Not Found")
        return f"Successfully Deleted file: {file_name}"
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not Responding")
    except StorageException:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Internal Error")

@router.post("/download",tags=["files"],description="This Routes is used to Download uploaded Files.")
def download_uploaded_file(id:int=Query(...,title="Enter filename"),user:str=Depends(get_current_verified_user),db:Session=Depends(get_db)):
    try:
        db_file=db.get(UserFile,id)
        if not db_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
        if db_file.username==user:
            drive=supabase.storage.from_('drive')
            download_file=drive.download(f"{user}/{db_file.stored_file_name}")
            print(f"{user}/{db_file.stored_file_name}")
            if download_file is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
            return Response(content=download_file,media_type=db_file.file_type,headers={
                "Content-Disposition":f'attachment; filename="{db_file.original_file_name}"',
            })
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not Responding")
    except StorageException:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Internal Error")

            
        
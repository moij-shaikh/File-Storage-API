from fastapi import APIRouter,Response,Depends,HTTPException,File,UploadFile,Form
from fastapi import status
from database import get_db,UserFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.exc import SQLAlchemyError
from storage3.utils import StorageException
from utils import scanner ,supabase 
from auth import get_current_verified_user
from schemas import Rename_file
import uuid


router=APIRouter(prefix="/file")

@router.post("",tags=["files"],description="This Routes is used to upload Files.")
async def upload_file(db:AsyncSession=Depends(get_db),user:str=Depends(get_current_verified_user),user_file:UploadFile=File(title="Choose file")):
    file_type=user_file.content_type
    allowed_files=["application/pdf","image/png","image/jpg","image/jpeg"]

    if file_type not in allowed_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Image not supported")
     
    scan_result=scanner.instream(user_file.file)
    if scan_result.get('stream')[0] !="OK":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Found virus ")
    user_file.file.seek(0)

    file_data=user_file.file.read()
    storage=supabase.storage.from_("drive")
    file_name=str(uuid.uuid4())
    original_file_name=user_file.filename
    file_path=f"{user}/{file_name}"

    try:
        storage.upload(
                    path=file_path,
                    file=file_data
                )
        db_file=UserFile(original_file_name=original_file_name,stored_file_name=file_name,username=user,file_type=file_type)
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
    except SQLAlchemyError :
        await db.rollback()
        storage.remove([file_path])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database error")
    except StorageException:
        raise HTTPException(detail="Storage Error",status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return {"ID":db_file.id,"Name":original_file_name}

@router.get("",tags=["files"],description="This Routes is used to View All uploaded Files.")
async def show_uploaded_file(db:AsyncSession=Depends(get_db),user:str=Depends(get_current_verified_user)):
    try:
        result=await db.execute(select(UserFile.id,UserFile.original_file_name).where(UserFile.username==user))
        db_files=result.all()
        if not db_files:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No files Found") 
        display_list=[
            {
                "id":file.id,
                "name":file.original_file_name
            }
            for file in db_files
        ]          
        return display_list
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database error")


@router.patch("/{id}",tags=["files"],description="This Routes is used to Rename uploaded Files.")
async def rename_uploaded_file(id:int,name:str=Form(),user:str=Depends(get_current_verified_user),db:AsyncSession=Depends(get_db)):
    try:
        db_file=await db.get(UserFile,id)
        if db_file is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File Not Found")
        if user == db_file.username:
            db_file.original_file_name=name
            await db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File Not Found")
        return "File Name Updated Successfully "
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not Responding")
    
@router.delete("/{id}",tags=["files"],description="This Routes is used to Delete uploaded Files.")
async def delete_uploaded_file(id:int,user:str=Depends(get_current_verified_user),db:AsyncSession=Depends(get_db)):  
    try:
        db_file=await db.get(UserFile,id)
        if db_file is None or db_file.username!=user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
        drive=supabase.storage.from_("drive")
        file_name=db_file.original_file_name
        stored_file=db_file.stored_file_name
        db.delete(db_file)
        drive.remove([f"{user}/{stored_file}"])
        await db.commit()
        return f"Successfully Deleted file: {file_name}"
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not Responding")
    except StorageException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Internal Error")

@router.get("/{id}",tags=["files"],description="This Routes is used to Download uploaded Files.")
async def download_uploaded_file(id:int,user:str=Depends(get_current_verified_user),db:AsyncSession=Depends(get_db)):
    try:
        db_file=await db.get(UserFile,id)
        if  db_file is None or db_file.username!=user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
        drive=supabase.storage.from_('drive')
        download_file=drive.download(f"{user}/{db_file.stored_file_name}")
        if download_file is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No File Found")
        return Response(content=download_file,media_type=db_file.file_type,headers={
            "Content-Disposition":f'attachment; filename="{db_file.original_file_name}"',
        })
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Database is not Responding")
    except StorageException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Internal Error")

            
        
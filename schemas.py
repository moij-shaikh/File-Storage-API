from pydantic import BaseModel ,Field

class Register_user(BaseModel):
    full_name:str
    username:str
    password:str
    email:str
    
class Rename_file(BaseModel):
    id:int=Field(...,title="Enter Id of File")
    name:str=Field(...,title="Enter New File Name")
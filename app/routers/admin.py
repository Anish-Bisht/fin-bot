from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from typing import List
from app.auth_deps import get_admin_user
from app.db import get_all_users, create_user, update_user_role, delete_user, add_document, remove_document, get_all_documents
import uuid

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    department: str

class UserUpdate(BaseModel):
    role: str
    department: str

class DocumentCreate(BaseModel):
    content: str
    required_role: str

@router.get("/users")
def get_users(admin: dict = Depends(get_admin_user)):
    return get_all_users()

@router.post("/users")
def add_user(user: UserCreate, admin: dict = Depends(get_admin_user)):
    success = create_user(user.username, user.password, user.role, user.department)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    return {"status": "User created successfully"}

@router.put("/users/{username}")
def edit_user_role(username: str, update: UserUpdate, admin: dict = Depends(get_admin_user)):
    success = update_user_role(username, update.role, update.department)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "User updated successfully"}

@router.delete("/users/{username}")
def remove_user(username: str, admin: dict = Depends(get_admin_user)):
    if username == admin["username"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    success = delete_user(username)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "User deleted successfully"}

@router.get("/documents")
def get_documents(admin: dict = Depends(get_admin_user)):
    return get_all_documents()

@router.post("/documents")
async def add_new_document(
    folder_name: str = Form(...),
    files: List[UploadFile] = File(...),
    admin: dict = Depends(get_admin_user)
):
    added_docs = []
    for file in files:
        content = await file.read()
        try:
            text_content = content.decode('utf-8', errors='ignore')
        except Exception:
            text_content = str(content)
            
        doc_id = str(uuid.uuid4())
        # Since user wanted 'required_role' removed from upload, default to 'all'
        add_document(doc_id, text_content, "all", folder_name, file.filename)
        added_docs.append(doc_id)
        
    return {"status": f"{len(files)} Document(s) added into {folder_name}", "ids": added_docs}

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, admin: dict = Depends(get_admin_user)):
    try:
        remove_document(doc_id)
        return {"status": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

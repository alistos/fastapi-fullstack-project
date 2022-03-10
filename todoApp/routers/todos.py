from http.client import responses
import sys
from sqlalchemy import false
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse

from uuid import UUID
from fastapi import Depends, HTTPException, APIRouter, Request, Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from .auth import get_usuario_atual, getUsuarioException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"descricao": "Todo não encontrado"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def lerTudoDoUsuario(request: Request, db: Session = Depends(get_db)):

    todos = db.query(models.Todos).filter(models.Todos.donoId == 1).all()

    return templates.TemplateResponse("home.html", {"request": request, "todos": todos})

@router.get("/add-todo", response_class=HTMLResponse)
async def addNovoTodo(request: Request):
    return templates.TemplateResponse("add-todo.html", {"request": request})

@router.post("/add-todo", response_class=HTMLResponse)
async def criarTodo(request: Request, titulo: str = Form(...), descricao: str = Form(...),
    prioridade: int = Form(...), db: Session = Depends(get_db)):

    todoModel = models.Todos()
    todoModel.titulo = titulo
    todoModel.descricao = descricao
    todoModel.prioridade = prioridade
    todoModel.completo = False
    todoModel.donoId = 1

    db.add(todoModel)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todoId}", response_class=HTMLResponse)
async def editTodo(request: Request, todoId: int, db: Session = Depends(get_db)):

    todo = db.query(models.Todos).filter(models.Todos.id == todoId).first()

    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo})

@router.post("/edit-todo/{todoId}", response_class=HTMLResponse)
async def atualizarTodo(request: Request, todoId: int, titulo: str =  Form(...),
    descricao: str = Form(...), prioridade: int = Form(...), db: Session = Depends(get_db)):

    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId).first()

    todoModel.titulo = titulo
    todoModel.descricao = descricao
    todoModel.prioridade = prioridade
    
    db.add(todoModel)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/deletar/{todoId}")
async def excluirTodo(request: Request, todoId: int, db: Session = Depends(get_db)):

    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId).\
        filter(models.Todos.donoId == 1).first()

    if todoModel is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todoId).delete()

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/completo/{todoId}", response_class=HTMLResponse)
async def completarTodo(request: Request, todoId: int, db: Session = Depends(get_db)):

    todo = db.query(models.Todos).filter(models.Todos.id == todoId).first()

    todo.completo = not todo.completo

    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
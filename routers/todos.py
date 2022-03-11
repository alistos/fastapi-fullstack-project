from http.client import responses
import sys
from sqlalchemy import false
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse

from fastapi import Depends, APIRouter, Request, Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from .auth import get_usuario_atual
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

    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todos = db.query(models.Todos).filter(models.Todos.donoId == user.get("id")).all()

    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})

@router.get("/add-todo", response_class=HTMLResponse)
async def addNovoTodo(request: Request):
    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})

@router.post("/add-todo", response_class=HTMLResponse)
async def criarTodo(request: Request, titulo: str = Form(...), descricao: str = Form(...),
    prioridade: int = Form(...), db: Session = Depends(get_db)):

    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todoModel = models.Todos()
    todoModel.titulo = titulo
    todoModel.descricao = descricao
    todoModel.prioridade = prioridade
    todoModel.completo = False
    todoModel.donoId = user.get("id")

    db.add(todoModel)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todoId}", response_class=HTMLResponse)
async def editTodo(request: Request, todoId: int, db: Session = Depends(get_db)):

    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todoId).first()

    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

@router.post("/edit-todo/{todoId}", response_class=HTMLResponse)
async def atualizarTodo(request: Request, todoId: int, titulo: str =  Form(...),
    descricao: str = Form(...), prioridade: int = Form(...), db: Session = Depends(get_db)):

    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId).first()

    todoModel.titulo = titulo
    todoModel.descricao = descricao
    todoModel.prioridade = prioridade
    
    db.add(todoModel)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/deletar/{todoId}")
async def excluirTodo(request: Request, todoId: int, db: Session = Depends(get_db)):

    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId).\
        filter(models.Todos.donoId == user.get("id")).first()

    if todoModel is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todoId).delete()

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/completo/{todoId}", response_class=HTMLResponse)
async def completarTodo(request: Request, todoId: int, db: Session = Depends(get_db)):

    user = await get_usuario_atual(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todoId).first()

    todo.completo = not todo.completo

    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
from http.client import responses
import sys
sys.path.append("..")

from uuid import UUID
from fastapi import Depends, HTTPException, APIRouter
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from .auth import get_usuario_atual, getUsuarioException
import models

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"descricao": "Todo não encontrado"}}
)

models.Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class Todo(BaseModel):
    titulo: str
    descricao: Optional[str] 
    prioridade: int = Field(gt=0, lt=6, description="A prioridade deve estar entre 1-5")
    completo: bool   

#Ler todos os todos
@router.get("/")
async def lerTodos(db: Session = Depends(get_db)):
    return db.query(models.Todos).all()

@router.get("/usuario")
async def lerTudoPorUsuario(user: dict = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    if user is None:
        raise getUsuarioException()
    return db.query(models.Todos).filter(models.Todos.donoId == user.get("id")).all()

#Encontrar todo pelo id
@router.get("/{todoId}")
async def lerTodo(todoId: int, user: dict = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    if user is None:
        raise getUsuarioException

    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId)\
    .filter(models.Todos.donoId == user.get("id")).first()

    if todoModel is not None:
        return todoModel

    raise http_exception()

#Adicionar Todo para o db
@router.post("/")
async def criarTodo(todo: Todo, user: dict = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    if user is None:
        raise getUsuarioException()
    todoModel = models.Todos()
    todoModel.titulo = todo.titulo
    todoModel.descricao = todo.descricao
    todoModel.prioridade = todo.prioridade
    todoModel.completo = todo.completo
    todoModel.donoId = user.get("id")

    db.add(todoModel)
    db.commit()

    succesful_response(201)

#Atualizar todo no db
@router.put("/{todoId}")
async def atualizarTodo(todoId: int, todo: Todo, user: dict = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    if user is None:
        raise getUsuarioException()
    
    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId).\
        filter(models.Todos.donoId == user.get("id")).first()

    if todoModel is None:
        raise http_exception()

    todoModel.titulo = todo.titulo
    todoModel.descricao = todo.descricao
    todoModel.prioridade = todo.prioridade
    todoModel.completo = todo.completo

    db.add(todoModel)
    db.commit()

    succesful_response(200)

#deleter todo no db
@router.delete("/{todoId}")
async def deletarTodo(todoId: int, user: dict = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    if user is None:
        raise getUsuarioException()

    todoModel = db.query(models.Todos).filter(models.Todos.id == todoId).\
        filter(models.Todos.donoId == user.get("id")).first()

    if todoModel is None:
        raise http_exception()

    db.query(models.Todos).filter(models.Todos.id).delete()
    db.commit()

    succesful_response(200)

def http_exception():
    return HTTPException(status_code=404, detail="Todo não encontrado")

def succesful_response(status_code: int):
    return{
        'status': status_code,
        'transaction': 'Successful'
    }

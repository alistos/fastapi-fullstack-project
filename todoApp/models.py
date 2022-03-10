from enum import unique
from operator import index
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Usuarios(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    nomeUsuario = Column(String, unique=True, index=True)
    primeiroNome = Column(String)
    ultimoNome = Column(String)
    senhaHashed = Column(String)
    ehAtivo = Column(Boolean, default=True)
    todos = relationship("Todos", back_populates="dono")

class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    descricao = Column(String)
    prioridade = Column(Integer)
    completo = Column(Boolean, default=False)
    donoId = Column(Integer, ForeignKey("usuarios.id"))
    dono = relationship("Usuarios", back_populates="todos")
import sys
sys.path.append("..")

from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError

CHAVE_SECRETA = "ASDnhabsdhbaASDhbasdKNZXCsnzjfqwjeierhusd"
ALGORITMO = "HS256"

class CriarUsuario(BaseModel):
    nomeUsuario: str
    email: Optional[str]
    primeiroNome: str
    ultimoNome: str
    senha: str

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

oauth2Bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Não autorizado"}}
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_password_hash(senha):
    return bcrypt_context.hash(senha)

def verificarSenha(senha, senhaHash):
    return bcrypt_context.verify(senha, senhaHash)

def autenticarUsuario(nomeUsuario: str, senha: str, db):
    usuario = db.query(models.Usuarios).filter(models.Usuarios.nomeUsuario ==
    nomeUsuario).first()

    if not usuario:
        return False
    if not verificarSenha(senha, usuario.senhaHashed):
        return False
    return usuario

def criarTokenAcesso(nomeUsuario: str, idUsuario: int, expires_delta: Optional[timedelta] = None):
    encode = {"sub": nomeUsuario, "id": idUsuario}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, CHAVE_SECRETA, algorithm=ALGORITMO)

async def get_usuario_atual(token: str = Depends(oauth2Bearer)):
    try:
        payload = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise getUsuarioException()
        return {"username": username, "id": user_id}

    except JWTError:
        raise getUsuarioException()


@router.post("/criar/usuario")
async def criarNovoUsuario(criarUsuario: CriarUsuario, db: Session = Depends(get_db)):
    criarUsuarioModel = models.Usuarios()
    criarUsuarioModel.email = criarUsuario.email
    criarUsuarioModel.nomeUsuario = criarUsuario.nomeUsuario
    criarUsuarioModel.primeiroNome = criarUsuario.primeiroNome
    criarUsuarioModel.ultimoNome = criarUsuario.ultimoNome

    senhaHash = get_password_hash(criarUsuario.senha)

    criarUsuarioModel.senhaHashed = senhaHash
    criarUsuarioModel.ehAtivo = True

    db.add(criarUsuarioModel)
    db.commit()

@router.post("/token")
async def loginParaTokenAcesso(dadosForm: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):

    usuario = autenticarUsuario(dadosForm.username, dadosForm.password, db)

    if not usuario:
        raise tokenException()
    token_expires = timedelta(minutes=20)
    token = criarTokenAcesso(usuario.nomeUsuario, usuario.id, expires_delta=token_expires)
    return token

#Exceções
def getUsuarioException():
    credentialsException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentialsException

def tokenException():
    tokenExceptionResponse = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nome de usuário ou senha incorretos",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return tokenExceptionResponse



import sys
sys.path.append("..")

from starlette.responses import RedirectResponse

from http.client import HTTPException
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

CHAVE_SECRETA = "ASDnhabsdhbaASDhbasdKNZXCsnzjfqwjeierhusd"
ALGORITMO = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

oauth2Bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Não autorizado"}}
)

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.senha: Optional[str] = None

    async def criarOauthForm(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.senha = form.get("senha")

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

async def get_usuario_atual(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            logout(request)
        return {"username": username, "id": user_id}

    except JWTError:
        raise HTTPException(status_code=404, detail="Não encontrado")

@router.post("/token")
async def loginParaTokenAcesso(response: Response, dadosForm: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):

    usuario = autenticarUsuario(dadosForm.username, dadosForm.senha, db)

    if not usuario:
        return False
    token_expires = timedelta(minutes=60)
    token = criarTokenAcesso(usuario.nomeUsuario, usuario.id, expires_delta=token_expires)

    response.set_cookie(key="access_token", value=token, httponly=True)

    return True

@router.get("/", response_class=HTMLResponse)
async def paginaAutenticacao(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.criarOauthForm()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

        validarCookieUsuario = await loginParaTokenAcesso(response=response, dadosForm=form, db=db)

        if not validarCookieUsuario:
            msg = "Username ou senha incorreta"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Erro desconhecido"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@router.get("/logout")
async def logout(request: Request):
    msg = "Logout realizado com sucesso"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response

@router.get("/registrar", response_class=HTMLResponse)
async def registrar(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/registrar", response_class=HTMLResponse)
async def registrarUsuario(request: Request, email: str = Form(...), username: str = Form(...),
    primeiroNome: str = Form(...), ultimoNome: str = Form(...),
    senha: str =  Form(...), senha2: str = Form(...), db: Session = Depends(get_db)):

    validacao1 = db.query(models.Usuarios).filter(models.Usuarios.nomeUsuario == username).first()

    validacao2 = db.query(models.Usuarios).filter(models.Usuarios.email == email).first()

    if senha != senha2 or validacao1 is not None or validacao2 is not None:
        msg = "Requisição de registro inválida"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

    usuarioModel = models.Usuarios()
    usuarioModel.nomeUsuario = username
    usuarioModel.email = email
    usuarioModel.primeiroNome = primeiroNome
    usuarioModel.ultimoNome = ultimoNome

    senhaHash = get_password_hash(senha)
    usuarioModel.senhaHashed = senhaHash
    usuarioModel.is_active = True

    db.add(usuarioModel)
    db.commit()

    msg = "Usuário criado com sucesso"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

import os
from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
from dotenv import load_dotenv

security = HTTPBasic()

# Загружаем переменные окружения из .env (если файл существует)
load_dotenv()


def parse_users():
    users_str = os.getenv("APP_USERS", "")
    users = {}
    if users_str:
        for pair in users_str.split(","):
            if ":" in pair:
                username, password = pair.strip().split(":", 1)
                users[username] = password
    return users


USERS = parse_users()
MCP_TOKEN = os.getenv("MCP_TOKEN", "")


def authenticate_http(credentials: Optional[HTTPBasicCredentials]):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required",
                    "details": None,
                }
            },
            headers={"WWW-Authenticate": "Basic"},
        )

    if (
        credentials.username not in USERS
        or USERS[credentials.username] != credentials.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid credentials",
                    "details": None,
                }
            },
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def authenticate_mcp(token: Optional[str]):
    if not MCP_TOKEN:
        return "mcp_user"

    if token != MCP_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid MCP token",
                    "details": None,
                }
            },
        )

    return "mcp_user"

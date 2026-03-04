import os
import uuid
import time
import zipfile
from datetime import datetime
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    BackgroundTasks,
    Header,
)
from fastapi.security import HTTPBasicCredentials
from fastapi.responses import FileResponse
from starlette.requests import Request

from auth import security, authenticate_http, authenticate_mcp
from rate_limit import check_rate_limit
from cleanup import cleanup_old_sessions, cleanup_archive
from logging_config import logger
from converters.docx_converter import convert_docx
from converters.xlsx_converter import convert_xlsx
from converters.pptx_converter import convert_pptx
from converters.pdf_converter import convert_pdf

app = FastAPI(title="Office to Markdown Converter")

MAX_FILE_SIZE = 30 * 1024 * 1024
STORAGE_DIR = "storage"

SUPPORTED_EXTENSIONS = {
    "docx": convert_docx,
    "xlsx": convert_xlsx,
    "pptx": convert_pptx,
    "pdf": convert_pdf,
}


@app.on_event("startup")
async def startup_event():
    cleanup_old_sessions()
    logger.info("Приложение запущено, очистка старых сессий выполнена")


def generate_session_id(username: str, extension: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"{timestamp}_{username}_{extension}_{short_uuid}"


def error_response(code: str, message: str, details=None):
    return {"error": {"code": code, "message": message, "details": details}}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/convert")
async def convert_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    credentials: HTTPBasicCredentials = Depends(security),
):
    username = authenticate_http(credentials)
    check_rate_limit(username)

    cleanup_old_sessions()

    filename = file.filename.lower()
    extension = filename.split(".")[-1] if "." in filename else ""

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "UNSUPPORTED_FILE_TYPE", f"File type .{extension} is not supported"
            ),
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=error_response("FILE_TOO_LARGE", "Maximum upload size is 30MB"),
        )

    session_id = generate_session_id(username, extension)
    session_dir = os.path.join(STORAGE_DIR, session_id)
    images_dir = os.path.join(session_dir, "images")
    md_path = os.path.join(session_dir, "document.md")
    archive_path = os.path.join(session_dir, "archive.zip")

    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    start_time = time.time()

    try:
        converter = SUPPORTED_EXTENSIONS[extension]
        markdown_content = converter(content, images_dir)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(md_path, f"{session_id}/document.md")

            if os.path.exists(images_dir) and os.listdir(images_dir):
                for img_name in os.listdir(images_dir):
                    img_path = os.path.join(images_dir, img_name)
                    zipf.write(img_path, f"{session_id}/images/{img_name}")

        processing_time = time.time() - start_time
        logger.info(
            f"username={username} | session_id={session_id} | "
            f"filename={file.filename} | size={file_size} | time={processing_time:.2f}s"
        )

        background_tasks.add_task(cleanup_archive, archive_path)

        return FileResponse(
            path=archive_path,
            media_type="application/zip",
            filename=f"{session_id}.zip",
        )

    except Exception as e:
        logger.error(f"username={username} | session_id={session_id} | error={str(e)}")
        raise HTTPException(
            status_code=500, detail=error_response("CONVERSION_ERROR", str(e))
        )


@app.post("/mcp/convert")
async def mcp_convert(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_mcp_token: str = Header(None, alias="X-MCP-Token"),
):
    username = authenticate_mcp(x_mcp_token)
    check_rate_limit(username)

    cleanup_old_sessions()

    filename = file.filename.lower()
    extension = filename.split(".")[-1] if "." in filename else ""

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                "UNSUPPORTED_FILE_TYPE", f"File type .{extension} is not supported"
            ),
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=error_response("FILE_TOO_LARGE", "Maximum upload size is 30MB"),
        )

    session_id = generate_session_id(username, extension)
    session_dir = os.path.join(STORAGE_DIR, session_id)
    images_dir = os.path.join(session_dir, "images")
    md_path = os.path.join(session_dir, "document.md")

    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    start_time = time.time()

    try:
        converter = SUPPORTED_EXTENSIONS[extension]
        markdown_content = converter(content, images_dir)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        processing_time = time.time() - start_time
        logger.info(
            f"username={username} | session_id={session_id} | "
            f"filename={file.filename} | size={file_size} | time={processing_time:.2f}s"
        )

        return {"session_id": session_id, "markdown_path": md_path}

    except Exception as e:
        logger.error(f"username={username} | session_id={session_id} | error={str(e)}")
        raise HTTPException(
            status_code=500, detail=error_response("CONVERSION_ERROR", str(e))
        )


@app.get("/mcp/resource/{session_id}")
async def mcp_resource(
    session_id: str, x_mcp_token: str = Header(None, alias="X-MCP-Token")
):
    authenticate_mcp(x_mcp_token)

    md_path = os.path.join(STORAGE_DIR, session_id, "document.md")

    if not os.path.exists(md_path):
        raise HTTPException(
            status_code=404,
            detail=error_response("INTERNAL_ERROR", "Session not found or expired"),
        )

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"session_id": session_id, "content": content}

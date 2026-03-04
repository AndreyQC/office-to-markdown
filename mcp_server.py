import os
import uuid

from dotenv import load_dotenv
from fastmcp import FastMCP

from converters.docx_converter import convert_docx
from converters.xlsx_converter import convert_xlsx
from converters.pptx_converter import convert_pptx
from converters.pdf_converter import convert_pdf


SUPPORTED_EXTENSIONS: dict[str, callable] = {
    "docx": convert_docx,
    "xlsx": convert_xlsx,
    "pptx": convert_pptx,
    "pdf": convert_pdf,
}

STORAGE_DIR = "storage"


# Загружаем переменные окружения из .env (если есть)
load_dotenv()

# FastMCP >= 3.x: режим JSON-ответа можно включить через переменную
# окружения FASTMCP_JSON_RESPONSE=true, поэтому флаг json_response
# в конструкторе больше не используется.
mcp = FastMCP("office-to-markdown")


@mcp.tool()
def convert_office_file(
    file_path: str,
) -> dict:
    """
    Конвертировать локальный файл (docx/xlsx/pptx/pdf) в Markdown.

    Аргументы:
      file_path: Абсолютный или относительный путь к файлу на диске.

    Возвращает:
      {
        "markdown": "...",
        "session_id": "...",
        "storage_path": "...",
      }
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path).lower()
    extension = filename.split(".")[-1] if "." in filename else ""

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise ValueError(f"Unsupported file type .{extension}. Supported: {supported}")

    with open(file_path, "rb") as f:
        content = f.read()

    session_id = f"mcp_{uuid.uuid4().hex[:12]}"
    session_dir = os.path.join(STORAGE_DIR, session_id)
    images_dir = os.path.join(session_dir, "images")
    md_path = os.path.join(session_dir, "document.md")

    os.makedirs(images_dir, exist_ok=True)

    converter = SUPPORTED_EXTENSIONS[extension]
    markdown_content = converter(content, images_dir)

    os.makedirs(session_dir, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return {
        "markdown": markdown_content,
        "session_id": session_id,
        "storage_path": os.path.abspath(session_dir),
    }


if __name__ == "__main__":
    # HTTP MCP-сервер (FastMCP >=3.x), к которому могут подключаться
    # несколько клиентов (OpenCode и др.) по одному URL.
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8787"))
    path = os.getenv("MCP_HTTP_PATH", "/mcp")

    mcp.run(transport="http", host=host, port=port, path=path)

# office-to-markdown

Микросервис для конвертации файлов `.docx`, `.xlsx`, `.pptx`, `.pdf` в Markdown с извлечением изображений.

## Требования

- [uv](https://docs.astral.sh/uv/) — менеджер пакетов и окружений (рекомендуется)
- Python 3.10+

Установка uv (если ещё не установлен):

```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Запуск локально

```bash
# Создание виртуального окружения (.venv)
uv venv

# Активация venv (опционально; uv run работает и без активации)
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# macOS / Linux:
# source .venv/bin/activate

# Установка зависимостей через uv
uv pip install -r requirements.txt

# Настройка переменных окружения через .env
cp .env.example .env
# Отредактируйте файл .env и задайте значения APP_USERS и MCP_TOKEN

# Запуск сервера (через uv — автоматически использует .venv)
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f
```

## API Endpoints

### Healthcheck

```bash
curl http://localhost:8000/health
```

### Конвертация файла (HTTP Basic)

```bash
curl -X POST "http://localhost:8000/convert" \
  -u user1:pass1 \
  -F "file=@document.docx" \
  --output result.zip
```

### MCP Endpoints (HTTP API)

**Конвертация:**

```bash
curl -X POST "http://localhost:8000/mcp/convert" \
  -H "X-MCP-Token: your-secret-mcp-token" \
  -F "file=@document.pdf"
```

**Получение содержимого:**

```bash
curl -X GET "http://localhost:8000/mcp/resource/{session_id}" \
  -H "X-MCP-Token: your-secret-mcp-token"
```

## MCP-сервер для OpenCode

Проект содержит отдельный MCP-сервер на основе `fastmcp` (`mcp_server.py`), который может работать как HTTP MCP-сервис и использоваться несколькими клиентами (OpenCode и др.).

### Запуск MCP-сервера (HTTP, один общий сервер)

```bash
# Установка зависимостей (если ещё не установлены)
uv pip install -r requirements.txt

# Запуск MCP-сервера (HTTP, FastMCP)
uv run --with fastmcp mcp_server.py
```

### Пример конфигурации OpenCode для remote MCP (`opencode.json`)

Если вы подняли MCP-сервер где-то снаружи (или локально, но по HTTP), несколько экземпляров OpenCode могут использовать один и тот же сервер:

```json
{
  "mcp": {
    "office-to-markdown-remote": {
      "type": "remote",
      "enabled": true,
      "url": "http://localhost:8787/mcp",
      "headers": {
        "Authorization": "Bearer your-secret-mcp-token"
      },
      "timeout": 10000
    }
  }
}
```
После этого сервер `office-to-markdown-remote` появится в списке MCP-серверов OpenCode, и вы сможете вызывать инструмент `convert_office_file` (принимает путь к локальному файлу и возвращает Markdown-содержимое и служебную информацию о сессии).

## Структура проекта

```
main.py              # HTTP API (FastAPI): /convert, /mcp/convert, /mcp/resource, /health
mcp_server.py        # MCP-сервер (FastMCP): инструмент convert_office_file
auth.py              # Аутентификация HTTP Basic и MCP Token
rate_limit.py        # Rate limiting (in-memory)
cleanup.py           # Очистка устаревших сессий и архивов
logging_config.py    # Конфигурация логирования
converters/          # Конвертеры форматов Office/PDF -> Markdown
  docx_converter.py
  xlsx_converter.py
  pptx_converter.py
  pdf_converter.py
storage/             # Временное хранение файлов и результатов конвертации
logs/                # Логи приложения
requirements.txt     # Python-зависимости (включая mcp, fastmcp и python-dotenv)
Dockerfile           # Сборка Docker-образа HTTP-сервиса
docker-compose.yml   # Запуск HTTP-сервиса через Docker Compose
.env.example         # Пример настроек окружения
.env                 # Локальные переменные окружения (не коммитить)
.venv/               # Виртуальное окружение (uv venv; в .gitignore)
```

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| APP_USERS      | Пользователи для HTTP Basic              | user1:pass1,user2:pass2      |
| MCP_TOKEN      | Токен для MCP аутентификации HTTP API    | your-secret-mcp-token        |
| MCP_HTTP_HOST  | Хост HTTP MCP-сервера (FastMCP)          | 0.0.0.0                      |
| MCP_HTTP_PORT  | Порт HTTP MCP-сервера (FastMCP)          | 8787                         |
| MCP_HTTP_PATH  | Путь HTTP MCP-сервера (FastMCP)          | /mcp                         |
| FASTMCP_JSON_RESPONSE | Включить JSON-ответы FastMCP           | true                         |

## Ограничения

- Максимальный размер файла: 30MB
- Rate limit: 10 запросов в минуту на пользователя
- TTL временных файлов: 1 час
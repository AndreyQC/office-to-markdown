---
order: 4
title: GPT prompt
---

Отлично. Конфигурация стала полностью консистентной.

Ниже -- **финальная, детерминированная версия MVP-internal промпта**, без неоднозначностей. Можно вставлять в Cursor/Claude.

---

## 🚀 FINAL PROMPT (MVP • Internal Tool • Deterministic)

Создай высокопроизводительный микросервис на **FastAPI**, который конвертирует файлы `.docx`, `.xlsx`, `.pptx`, `.pdf` в Markdown с извлечением изображений.

Сервис работает как HTTP API и как **MCP (Model Context Protocol) сервер**.

Проект предназначен для **internal использования**, один инстанс, без горизонтального масштабирования.

---

## 1️⃣ Безопасность

## HTTP API

-  Использовать [`fastapi.security`](http://fastapi.security)`.HTTPBasic`

-  Пользователи берутся из переменной окружения:

   ```
   APP_USERS=user1:pass1,user2:pass2
   
   ```

## MCP

-  Аутентификация через заголовок:

   ```
   X-MCP-Token: <token>
   
   ```

-  Токен хранится в переменной окружения:

   ```
   MCP_TOKEN=<secret>
   
   ```

---

## 2️⃣ Ограничения

-  Максимальный размер upload: **30MB**

-  Rate limiting: **10 запросов в минуту на пользователя**

-  Реализация rate limit -- **in-memory**

-  Single instance

-  Streaming upload (не загружать файл полностью в память)

---

## 3️⃣ Session ID

Формат:

```
[YYYYMMDDHHMMSS]_[username]_[extension]_[uuid4]
```

Пример:

```
20260302153045_alex_pdf_f47ac10b
```

UUID обязателен.

---

## 4️⃣ Структура хранения

Использовать директорию:

```
storage/
```

Структура:

```
storage/<session_id>/
    document.md
    images/
    archive.zip
```

---

## 5️⃣ TTL и очистка

-  TTL временных файлов: **1 час**

-  Cleanup:

   -  Запускается при старте приложения

   -  Проверяется после каждого запроса

-  Удаляются:

   -  Старые директории в `storage/`

   -  Старые архивы

---

## 6️⃣ Структура ZIP

Архив должен содержать:

```
<session_id>/
    document.md
    images/
        img_1.png
        img_2.png
```

В Markdown:

```
![image](images/img_1.png)
```

После отправки ответа архив удаляется через `BackgroundTasks`.

---

## 7️⃣ Конвертеры

## DOCX

-  `python-docx`

-  Сохранять заголовки

-  Сохранять таблицы

## XLSX

-  `pandas` + `openpyxl`

-  Сохранять **только значения**

-  Каждый лист:

   ```
   ## SheetName
   
   ```

-  Использовать `tabulate`

-  Без формул

## PPTX

-  `python-pptx`

-  Извлекать текст

-  Извлекать изображения

## PDF

-  `PyMuPDF (fitz)` -- текст и изображения

-  `pdfplumber` -- таблицы

-  Если таблица извлечена некорректно -> вставлять raw text

-  Если текстового слоя нет -> извлекать только изображения

-  OCR НЕ использовать

---

## 8️⃣ Логирование

Использовать `logging`:

-  `TimedRotatingFileHandler`

-  Ротация: ежедневно

-  Retention: **14 дней**

-  Логи сохранять в `logs/`

Логировать:

-  username

-  session_id

-  filename

-  file size

-  processing time

-  errors

---

## 9️⃣ JSON Error Schema

Единый формат ошибок:

```
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "Maximum upload size is 30MB",
    "details": null
  }
}
```

Коды:

-  FILE_TOO_LARGE

-  UNAUTHORIZED

-  RATE_LIMIT_EXCEEDED

-  UNSUPPORTED_FILE_TYPE

-  CONVERSION_ERROR

-  INTERNAL_ERROR

---

## 🔟 MCP

Интегрировать Python MCP SDK.

## Tool:

`convert_to_markdown`

-  Принимает файл

-  Возвращает путь к итоговому `.md`

## Resource:

Позволяет читать `.md` через MCP

## Transport:

-  SSE только для MCP

-  HTTP API -- без SSE

---

## 1️⃣1️⃣ Healthcheck

Endpoint:

```
GET /health
```

Ответ:

```
{
  "status": "ok"
}
```

---

## 1️⃣2️⃣ Docker

## Dockerfile

-  base: `python:3.10-slim`

-  Установить системные зависимости

-  Создать пользователя `appuser`

-  Запуск от `appuser`

## Docker Compose

-  Проброс порта 8000

-  Переменные:

   -  APP_USERS

   -  MCP_TOKEN

---

## 1️⃣3️⃣ Структура проекта

```
main.py
auth.py
rate_limit.py
cleanup.py
logging_config.py
converters/
    docx_converter.py
    xlsx_converter.py
    pptx_converter.py
    pdf_converter.py
storage/
logs/
requirements.txt
README.md
```

---

## 1️⃣4️⃣ README

Включить:

-  запуск локально

-  запуск через Docker

-  пример запроса curl

-  пример MCP подключения

---

## ✅ Результат

Код должен быть:

-  модульный

-  с комментариями на русском

-  без лишней абстракции

-  подходящий для internal MVP

-  без Kubernetes и Redis

---

Если хочешь, дальше могу:

-  🔍 сделать архитектурный sanity-check

-  🧠 провести быстрый threat-model

-  ⚙ оптимизировать prompt под Claude Code (чтобы меньше ошибался)

-  📦 подготовить версию с async file IO

Какой следующий шаг?
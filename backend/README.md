# PSY OS — Backend MVP

Операційна система для психологів. MVP: auth, клієнти, сесії, нотатки (текст/файл), чат, домашки, SOS, заглушка оплати, AI (опційно).

## Стек

- **FastAPI** — API
- **PostgreSQL + pgvector** — дані + embeddings
- **Redis** — ліміти AI + кеш
- **OpenAI** — summary, embeddings, pre-brief (можна вимкнути)

## Швидкий старт

### 1. Docker (PostgreSQL + Redis)

```bash
docker compose up -d
```

### 2. Python

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
```

### 3. Запуск API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## AI (опційно)

У `.env`:

```env
OPENAI_API_KEY=sk-...
AI_ENABLED=true
```

Без ключа AI працює в режимі заглушки — нотатки зберігаються, AI не викликається.

### Економія на AI

- `gpt-4o-mini` для summary/brief
- embeddings тільки при новій нотатці
- Redis-кеш + ліміт `AI_MAX_REQUESTS_PER_PSYCHOLOGIST_PER_DAY=20`

## Мови (i18n)

Заголовок запиту:

```
X-Locale: uk
```

або

```
X-Locale: en
```

## Основні endpoints

| Метод | URL | Опис |
|-------|-----|------|
| POST | `/api/v1/auth/psychologist/register` | Реєстрація психолога |
| POST | `/api/v1/auth/psychologist/login` | Вхід психолога |
| POST | `/api/v1/auth/client/login` | Вхід клієнта (login + password) |
| POST | `/api/v1/clients` | Створити клієнта (психолог) |
| GET | `/api/v1/clients` | Список клієнтів |
| POST | `/api/v1/sessions` | Запланувати сесію |
| POST | `/api/v1/notes/text` | Текстова нотатка + AI |
| POST | `/api/v1/notes/upload` | Файл/голос (multipart) |
| POST | `/api/v1/notes/client/{id}/pre-brief` | «Підготуй мене» |
| GET/POST | `/api/v1/messages/{client_id}` | Чат |
| POST | `/api/v1/homework` | Домашка |
| POST | `/api/v1/sos` | SOS (клієнт) |
| POST | `/api/v1/payments/stub` | Заглушка оплати |

Authorization: `Bearer <access_token>`

## Варіант A (MVP)

Без Zoom. Психолог після сесії:
- пише текст
- завантажує файл
- пізніше: голос → Whisper (v1.1)

## Наступні кроки

1. Підключити frontend до API
2. Whisper для голосових
3. Timeline, heatmap, graph
4. Railway deploy
5. Realtime WebSocket для чату/SOS

## Структура

```
backend/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   ├── services/
│   └── i18n/locales/uk.json, en.json
├── requirements.txt
└── .env.example
```

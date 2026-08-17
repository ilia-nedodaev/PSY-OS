# PSY OS — Деплой на бесплатный HTTP хостинг (Render + Neon)

Полный продукт **без AI** (`AI_ENABLED=false`).  
Когда будете готовы — вставьте `OPENAI_API_KEY` и поставьте `AI_ENABLED=true`.

---

## Шаг 1: База данных (Neon — бесплатно)

1. Зайдите на [neon.tech](https://neon.tech) → Sign up  
2. Create project → регион **EU** (Frankfurt)  
3. Скопируйте **Connection string** (PostgreSQL)  
4. Формат будет примерно:
   ```
   postgresql://user:pass@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
   ```
   Backend сам преобразует в `postgresql+asyncpg://`

---

## Шаг 2: GitHub репозиторий

1. Создайте репозиторий на GitHub  
2. Загрузите папку `PSY OS` целиком  
3. Убедитесь что есть: `Dockerfile`, `render.yaml`, `backend/`, `frontend/`

---

## Шаг 3: Render (бесплатный HTTP хостинг)

1. [render.com](https://render.com) → Sign up  
2. **New → Blueprint** → подключите GitHub репо  
3. Render прочитает `render.yaml`  
4. В переменных окружения укажите:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | строка из Neon |
| `SECRET_KEY` | любая длинная случайная строка (64+ символов) |
| `AI_ENABLED` | `false` |
| `SERVE_FRONTEND` | `true` |
| `CORS_ORIGINS` | `*` |

5. Deploy → получите URL вида:
   ```
   https://psyos-xxxx.onrender.com
   ```
   (бесплатный план = HTTP/HTTPS, может «засыпать» после 15 мин неактivity)

---

## Шаг 4: Проверка

- Главная: `https://ваш-url.onrender.com/`
- API docs: `https://ваш-url.onrender.com/docs`
- Health: `https://ваш-url.onrender.com/api/v1/health`

---

## Локальный запуск (до деплоя)

```bash
docker compose up -d
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Откройте: http://localhost:8000

---

## Что работает без AI

| Функция | Статус |
|---------|--------|
| Регистрация / вход психолога | ✅ |
| Создание клиентов | ✅ |
| Вход клиента (login + password) | ✅ |
| Календарь / сессии | ✅ |
| Нотатки (текст) | ✅ |
| Загрузка файлов | ✅ |
| Timeline (ручной) | ✅ |
| Чат | ✅ |
| Домашки | ✅ |
| SOS | ✅ |
| Оплата (заглушка) | ✅ |
| AI summary / memory | 🔌 готово, выключено |

---

## Когда подключите AI

В Render → Environment:

```env
OPENAI_API_KEY=sk-...
AI_ENABLED=true
```

Перезапустите сервис. Без изменений кода заработают:
- AI summary после нотатки
- Pre-brief «Подготовь меня»
- Embeddings для будущего AI Memory

---

## Redis (опционально)

На бесплатном старте **Redis не обязателен** — AI-кеш и лимиты просто пропускаются.

Позже: [upstash.com](https://upstash.com) → free Redis → добавьте `REDIS_URL`.

---

## Безопасность (production)

1. Смените `SECRET_KEY` на уникальный  
2. `CORS_ORIGINS` → ваш домен  
3. Neon + Render в регионе EU  
4. HTTPS включён на Render автоматически  

---

## Структура проекта

```
PSY OS/
├── frontend/          ← сайт + кабинеты
├── backend/           ← API
├── docker-compose.yml ← локальная БД
├── Dockerfile         ← деплой
├── render.yaml        ← конфиг Render
└── DEPLOY.md          ← эта инструкция
```

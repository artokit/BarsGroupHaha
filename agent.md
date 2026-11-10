# agent.md

Правила разработки проекта. Сейчас описан только Telegram-бот (`telegram-bot/`). Раздел по FastAPI добавим позже.

## Стек

- Python 3.11+
- aiogram 3
- PostgreSQL (драйвер `asyncpg`)
- SQLAlchemy 2 (async)
- Alembic

## Ограничения для ИИ-агента (обязательно)

- **Агенту запрещено запускать бота.** Никаких `python main.py`, `start_polling`, `docker compose up` для сервиса `bot`, фоновых процессов и автозапуска после правок.
- **Агенту запрещено тестировать бота через Telegram:** `getMe`, `getUpdates`, `getWebhookInfo`, отправка сообщений, установка/снятие вебхука, любые запросы к `api.telegram.org` с токеном.
- **Причина:** у Telegram один `getUpdates` на токен. Второй экземпляр получает `409 Conflict`, апдейты теряются, реальный бот перестаёт отвечать.
- Запускает и проверяет бота **только разработчик вручную**. Агент может читать код, править код, объяснять и писать тесты, но не выполнять их с реальным токеном.
- `.env` с реальным `BOT_TOKEN` не читать в логи, не выводить в ответы, не коммитить.
- Если для проверки нужен запуск — агент пишет, что именно и какой командой запустить, и ждёт, пока это сделает разработчик.

## Структура

```
telegram-bot/
├── main.py                 # запуск бота, только wiring
├── config.py               # настройки (токен, DATABASE_URL)
│
├── routers/                # presentation
│   ├── __init__.py         # общий список роутеров для include_router
│   ├── start.py
│   └── profile.py
│
├── services/               # application
│   ├── user_service.py
│   └── order_service.py
│
├── repositories/           # доступ к данным
│   ├── base.py
│   ├── user_repository.py
│   └── order_repository.py
│
├── db/                     # инфраструктура БД
│   ├── base.py             # DeclarativeBase
│   ├── models.py           # SQLAlchemy-модели
│   ├── session.py          # engine, async_sessionmaker, get_session
│   └── migrations/         # Alembic (env.py, versions/)
│
├── keyboards/              # клавиатуры
│   ├── reply.py
│   └── inline.py
│
├── states.py               # FSM StatesGroup
└── middlewares/
    ├── db.py               # сессия + репозитории/сервисы в data
    └── __init__.py
```

## Слои

| Папка | Слой | Что внутри | Чего быть не должно |
|---|---|---|---|
| `routers/` | presentation | хендлеры, `Message`/`CallbackQuery`, вызов сервисов, ответы | SQL, `select()`, бизнес-правила |
| `keyboards/`, `states.py` | presentation | клавиатуры, FSM | логика |
| `services/` | application | сценарии: проверить → вызвать репозиторий → вернуть результат | aiogram-типы, SQL-запросы, работа с `Message` |
| `repositories/` | repositories | CRUD/запросы к БД, принимают `AsyncSession` | формирование текстов/клавиатур, вызов хендлеров |
| `db/` | инфраструктура | подключение, модели, миграции | бизнес-логика |

Поток вызова: **router → service → repository → db**.

- `router` — распарсил апдейт → вызвал `service.create_user(...)` → отправил ответ.
- `service` — единственное место с бизнес-правилами; зависит от репозитория через конструктор.
- `repository` — единственное место с запросами к БД.
- `db` — только подключение и модели.

Отдельный слой `domain` не вводим: правила живут в сервисах и моделях. Если проект вырастет — вынесем отдельно.

## PostgreSQL + Alembic

- Драйвер `asyncpg`, URL вида `postgresql+asyncpg://user:pass@host:5432/db` в `config.py` (значение из `.env`).
- `db/session.py`: `create_async_engine`, `async_sessionmaker`, `get_session()`.
- Alembic живёт в `db/migrations/`, `target_metadata = Base.metadata`, `env.py` настроен под async engine.
- Любое изменение схемы: правим `db/models.py` → `alembic revision --autogenerate -m "..."` → `alembic upgrade head`.
- Схему руками в БД не меняем, только через миграции.

## Правила

1. Хендлер не делает запросов к БД и не содержит условий бизнес-логики.
2. Сервис не импортирует `aiogram`; хендлер не импортирует `sqlalchemy`.
3. Репозиторий не формирует сообщения и клавиатуры.
4. Сессия, репозиторий и сервис попадают в хендлер через middleware и не создаются внутри хендлера.
5. Ошибки сервиса ловятся в хендлере или общем error-handler и превращаются в понятный пользователю текст.
6. FSM-состояния — в `states.py`; данные шага — в `state_data`/DTO, без глобальных переменных.
7. Конфиг только через `config.py`, `os.getenv` по коду не размазываем.
8. Для любой правки схемы БД обязательна Alembic-миграция.
9. Одновременно работает только один экземпляр бота; `409 Conflict` в логах = где-то запущен второй.
10. Запуск и тестирование бота выполняет только разработчик (см. «Ограничения для ИИ-агента»).

## Чек-лист новой фичи

1. Модель (если нужна новая таблица) в `db/models.py` + миграция.
2. Методы работы с данными — в `repositories/`.
3. Сценарий и правила — в `services/`.
4. Клавиатуры — в `keyboards/`, состояния — в `states.py`.
5. Хендлер — в `routers/`, регистрация роутера в `routers/__init__.py`.
6. Зависимости прокинуть через `middlewares/db.py`.

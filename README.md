# 🧭 Smart Trip Copilot - Samarkand

**AI-планировщик путешествий по Узбекистану с Hybrid RAG и локальной LLM**

MVP для хакатона: превращает текстовый/голосовой запрос в проверенный маршрут.

---

## ✨ Возможности

- 🎤 **Intake Agent** — парсинг естественного языка → структурированный JSON
- 🔍 **Hybrid RAG** — фильтры по метаданным + семантический поиск
- 🗺️ **Route Planner** — генерация 3 вариантов маршрута
- ✅ **Verifier** — проверка бюджета, времени, ограничений
- 🦙 **Local LLM** — работает с Ollama (без API затрат)

---

## 📊 Данные

| Тип | Количество |
|-----|------------|
| POI (достопримечательности) | 30 мест |
| Шаблоны маршрутов | 6 вариантов |
| Категории советов | 12 |
| Горные маршруты | 4 опции |

---

## 🚀 Быстрый старт

### 1. Установка

```bash
cd c:\Users\hp\Desktop\Samarkand_Hacakton

# Основные зависимости
python -m pip install pydantic rich python-dotenv

# Опционально: векторный поиск
python -m pip install chromadb sentence-transformers
```

### 2. Настройка LLM

**Вариант A: Ollama (рекомендуется)**
```bash
# Установите Ollama: https://ollama.com/download
ollama pull llama3.2
ollama serve
```

**Вариант B: OpenAI**
```bash
copy .env.example .env
# Добавьте OPENAI_API_KEY в .env
```

### 3. Тестирование

```bash
python test_pipeline.py
```

### 4. Запуск демо

```bash
python demo.py
python demo.py "2 дня Самарканд, $100, на 2-й день горы"
```

---

## 📁 Структура

```
📦 Samarkand_Hacakton/
├── 📄 demo.py              # CLI демо
├── 📄 test_pipeline.py     # Тесты компонентов
├── 📁 data/
│   ├── poi.json           # 30 POI Самарканда
│   ├── routes.json        # 6 шаблонов маршрутов
│   └── tips.json          # Советы и рекомендации
├── 📁 src/
│   ├── agents/
│   │   ├── intake.py      # Парсинг запроса
│   │   ├── planner.py     # Генерация маршрутов
│   │   └── verifier.py    # Проверка выполнимости
│   ├── rag/
│   │   └── retriever.py   # Hybrid RAG
│   ├── models/
│   │   └── schemas.py     # Pydantic схемы
│   └── utils/
│       └── llm.py         # Ollama + OpenAI
└── 📁 docs/
    └── OLLAMA_SETUP.md    # Настройка локальной LLM
```

---

## 🎯 Архитектура Hybrid RAG

```
┌─────────────────────────────────────────────────────────┐
│                    User Input                            │
│  "2 дня Самарканд, $100, на 2-й день горы"              │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Intake Agent: Text → TripRequest JSON                  │
│  {city, days, budget, interests, constraints}           │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Hybrid RAG Retriever                                   │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Metadata Filter │ + │ Semantic Search │              │
│  │ (deterministic) │   │ (embeddings)    │              │
│  └─────────────────┘  └─────────────────┘              │
│  Фильтры гарантируют ограничения                        │
│  Embeddings дают умный подбор                           │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Route Planner                                          │
│  Template matching + Dynamic generation                 │
│  → 3 варианта (budget / balanced / comfort)            │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Verifier Agent                                         │
│  ✓ Budget check  ✓ Time check  ✓ Constraints check     │
│  → Auto-fixes + Recommendations                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Пример вывода

```
📋 TripRequest:
   Город: Samarkand
   Дней: 2
   Бюджет: $100
   Интересы: ['history', 'nature']
   Ограничения: ['mountains on day 2']

🗺️ Вариант 1: Классический Самарканд с горами
   💰 $58 | 📅 2 days | balanced
   Day 1: Исторический центр (6 activities)
   Day 2: Горы и природа 🏔️ (1 activity)

✅ FEASIBLE (score: 100%)
   Budget OK: $58 из $100
   Constraints OK: mountains on day 2 ✓
```

---

## 🛠️ Расширение данных

Добавьте больше POI в `data/poi.json`:

```json
{
  "id": "new_place",
  "name": "Название",
  "category": ["history", "architecture"],
  "cost_usd": 5,
  "duration_hours": 1.5,
  "tags": ["must-see", "photography"],
  "coordinates": {"lat": 39.65, "lng": 66.97}
}
```

---

## 📖 Документация

- [Настройка Ollama](docs/OLLAMA_SETUP.md)
- [Сбор данных](DATA_COLLECTION.md)
- [План хакатона](HACKATHON_PLAN.md)

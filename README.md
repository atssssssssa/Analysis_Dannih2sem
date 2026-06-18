# Задание 2 — API-пайплайн: данные → LLM → результат

Скрипт читает данные студентов из CSV-файла, отправляет информацию о каждом студенте в LLM через OpenRouter API и сохраняет структурированный результат в JSON.

Задача — анализ успеваемости студентов: скрипт читает данные студента → LLM определяет уровень успеваемости, составляет краткий профиль и даёт рекомендацию по обучению → результат сохраняется в JSON.

## Запуск

1. Установить зависимости:

```bash
pip install openai python-dotenv
````

2. Создать файл `.env` с ключом:

```env
OPENROUTER_API_KEY=your_api_key_here
```

3. Запустить скрипт:

```bash
python main.py StudentsPerformance.csv
```

Результат сохраняется в файл:

```text
StudentsPerformance_results.json
```

рядом с входным CSV-файлом.

## Пример входных данных (`StudentsPerformance.csv`)

```csv
gender,race/ethnicity,parental level of education,lunch,test preparation course,math score,reading score,writing score
female,group B,bachelor's degree,standard,none,72,72,74
male,group C,some college,standard,completed,69,90,88
female,group B,master's degree,standard,none,90,95,93
```

## Пример выходных данных (`StudentsPerformance_results.json`)

```json
[
  {
    "student_id": 1,
    "gender": "female",
    "race_ethnicity": "group B",
    "parental_level_of_education": "bachelor's degree",
    "lunch": "standard",
    "test_preparation_course": "none",
    "math_score": 72,
    "reading_score": 72,
    "writing_score": 74,
    "average_score": 72.67,
    "strongest_subject": "writing",
    "weakest_subject": "math",
    "calculated_performance_level": "medium",
    "llm_performance_level": "medium",
    "student_profile": "Female student in group B, parents hold a bachelor's degree, receives standard lunch, did not take a preparatory course. Scores: Math 72, Reading 72, Writing 74 (average 72.67). Strongest subject is Writing; weakest is Math.",
    "recommendation": "Focus on improving Math skills through targeted practice, supplemental tutoring, and leveraging her strong writing abilities to explain mathematical concepts. Incorporate problem‑solving workshops and regular feedback to raise her Math performance toward the 80+ range."
  },
  {
    "student_id": 2,
    "gender": "female",
    "race_ethnicity": "group C",
    "parental_level_of_education": "some college",
    "lunch": "standard",
    "test_preparation_course": "completed",
    "math_score": 69,
    "reading_score": 90,
    "writing_score": 88,
    "average_score": 82.33,
    "strongest_subject": "reading",
    "weakest_subject": "math",
    "calculated_performance_level": "medium",
    "llm_performance_level": "high",
    "student_profile": "Female student in group C, parents have some college education, receives standard lunch, completed a preparatory course. Excels in reading (90) and writing (88) but struggles with mathematics (69), yielding an overall average of 82.33.",
    "recommendation": "Maintain strengths in reading and writing through enrichment activities, while allocating additional time and targeted support for math—such as tutoring, practice problem sets, and concept‑focused workshops—to raise the math score and sustain overall high performance."
  }
]

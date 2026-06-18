import csv
import json
import os
import sys
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

REQUIRED_COLUMNS = [
    "gender",
    "race/ethnicity",
    "parental level of education",
    "lunch",
    "test preparation course",
    "math score",
    "reading score",
    "writing score",
]

MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b:free"


def get_level(avg_score: float) -> str:
    if avg_score >= 85:
        return "high"
    if avg_score >= 60:
        return "medium"
    return "low"


def make_local_profile(level: str, strongest_subject: str, weakest_subject: str) -> dict:
    """Fallback-анализ без API, чтобы файл создавался даже без OPENROUTER_API_KEY."""
    if level == "high":
        profile = "Студент показывает высокий уровень успеваемости и уверенно справляется с заданиями."
        recommendation = f"Поддерживать высокий темп обучения и давать дополнительные задания по {strongest_subject}."
    elif level == "medium":
        profile = "Студент показывает средний уровень успеваемости, но есть зоны для улучшения."
        recommendation = f"Регулярно тренировать {weakest_subject} и закреплять базовые темы."
    else:
        profile = "Студенту требуется дополнительная поддержка и повторение базового материала."
        recommendation = f"Составить индивидуальный план и уделить больше внимания предмету {weakest_subject}."

    return {
        "performance_level": level,
        "student_profile": profile,
        "recommendation": recommendation,
    }


def ask_llm(client, row, math_score, reading_score, writing_score, average_score, strongest_subject, weakest_subject):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": f"""
                Проанализируй данные студента.
                Нужно определить:
                1. Общий уровень успеваемости: high / medium / low
                2. Краткий профиль студента
                3. Практическую рекомендацию по обучению
            Верни ответ строго в JSON формате:

{{
  "performance_level": "high | medium | low",
  "student_profile": "...",
  "recommendation": "..."
}}

Данные студента:
- Пол: {row['gender']}
- Группа: {row['race/ethnicity']}
- Образование родителей: {row['parental level of education']}
- Тип питания: {row['lunch']}
- Подготовительный курс: {row['test preparation course']}
- Математика: {math_score}
- Чтение: {reading_score}
- Письмо: {writing_score}
- Средний балл: {average_score}
- Сильнейший предмет: {strongest_subject}
- Самый слабый предмет: {weakest_subject}
""",
            }
        ],
    )

    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


def save_results(output_file: str, results: list) -> None:
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Ошибка: Не указан файл для обработки")
        print("Использование: python3 main.py <файл.csv> [limit]")
        print("Пример: python3 main.py StudentsPerformance.csv 20")
        sys.exit(1)

    input_file = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) >= 3 else None

    if not os.path.exists(input_file):
        print(f"Ошибка: Файл '{input_file}' не существует")
        sys.exit(1)

    output_file = os.path.splitext(input_file)[0] + "_results.json"

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    client = None
    use_llm = bool(api_key)
    if use_llm and OpenAI is not None:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    else:
        use_llm = False
        print("OPENROUTER_API_KEY или библиотека openai не найдены. Будет использован локальный анализ без LLM.")

    results = []

    with open(input_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing_columns:
            print("Ошибка: В CSV не хватает колонок:")
            print(", ".join(missing_columns))
            sys.exit(1)

        for index, row in enumerate(reader, start=1):
            if limit is not None and index > limit:
                break

            math_score = int(row["math score"])
            reading_score = int(row["reading score"])
            writing_score = int(row["writing score"])

            scores = {
                "math": math_score,
                "reading": reading_score,
                "writing": writing_score,
            }

            average_score = round(sum(scores.values()) / len(scores), 2)
            strongest_subject = max(scores, key=scores.get)
            weakest_subject = min(scores, key=scores.get)
            calculated_level = get_level(average_score)

            parsed = None
            if use_llm:
                try:
                    parsed = ask_llm(
                        client,
                        row,
                        math_score,
                        reading_score,
                        writing_score,
                        average_score,
                        strongest_subject,
                        weakest_subject,
                    )
                except Exception as error:
                    print(f"LLM ошибка у студента #{index}: {error}")
                    print("Использую локальный анализ для этой строки.")
                    parsed = make_local_profile(calculated_level, strongest_subject, weakest_subject)
            else:
                parsed = make_local_profile(calculated_level, strongest_subject, weakest_subject)

            results.append(
                {
                    "student_id": index,
                    "gender": row["gender"],
                    "race_ethnicity": row["race/ethnicity"],
                    "parental_level_of_education": row["parental level of education"],
                    "lunch": row["lunch"],
                    "test_preparation_course": row["test preparation course"],
                    "math_score": math_score,
                    "reading_score": reading_score,
                    "writing_score": writing_score,
                    "average_score": average_score,
                    "strongest_subject": strongest_subject,
                    "weakest_subject": weakest_subject,
                    "calculated_performance_level": calculated_level,
                    "llm_performance_level": parsed.get("performance_level", calculated_level),
                    "student_profile": parsed.get("student_profile", ""),
                    "recommendation": parsed.get("recommendation", ""),
                }
            )

            save_results(output_file, results)
            print(f"Обработан студент #{index}: средний балл {average_score}")

    save_results(output_file, results)
    print(f"Данные сохранены в {output_file}")


if __name__ == "__main__":
    main()

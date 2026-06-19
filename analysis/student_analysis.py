from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

SCORE_COLUMNS = ["math score", "reading score", "writing score"]
REQUIRED_COLUMNS = [
    "gender",
    "race/ethnicity",
    "parental level of education",
    "lunch",
    "test preparation course",
    *SCORE_COLUMNS,
]


def safe_filename(name: str) -> str:
    name = Path(name).name
    return re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ._ -]", "_", name)


def is_allowed_file(file_name: str) -> bool:
    return Path(file_name).suffix.lower() in {".csv", ".xlsx", ".xls"}


def read_dataset(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("Неподдерживаемый формат файла. Нужен .csv, .xlsx или .xls")


def _round_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 2)


def validate_student_columns(df: pd.DataFrame) -> list[str]:
    columns_lower = {str(col).strip().lower(): col for col in df.columns}
    missing = [col for col in REQUIRED_COLUMNS if col not in columns_lower]
    return missing


def analyze_student_dataset(file_path: str | Path, output_dir: str | Path) -> tuple[dict[str, Any], str]:
    path = Path(file_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    df = read_dataset(path)
    df.columns = [str(col).strip() for col in df.columns]

    missing_required = validate_student_columns(df)

    numeric_stats: dict[str, dict[str, Any]] = {}
    existing_score_cols = [col for col in SCORE_COLUMNS if col in df.columns]
    for col in existing_score_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        numeric_stats[col] = {
            "count": int(series.count()),
            "min": _round_float(series.min()),
            "max": _round_float(series.max()),
            "mean": _round_float(series.mean()),
            "median": _round_float(series.median()),
            "std": _round_float(series.std()),
        }

    if existing_score_cols:
        df["average score"] = df[existing_score_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)

    categorical_columns = [
        "gender",
        "race/ethnicity",
        "parental level of education",
        "lunch",
        "test preparation course",
    ]
    top_values: dict[str, dict[str, int]] = {}
    for col in categorical_columns:
        if col in df.columns:
            top_values[col] = {str(k): int(v) for k, v in df[col].value_counts(dropna=False).head(10).items()}

    group_insights: dict[str, Any] = {}
    if "test preparation course" in df.columns and "average score" in df.columns:
        group_insights["average_by_test_preparation"] = {
            str(k): _round_float(v)
            for k, v in df.groupby("test preparation course")["average score"].mean().sort_values(ascending=False).items()
        }
    if "gender" in df.columns and "average score" in df.columns:
        group_insights["average_by_gender"] = {
            str(k): _round_float(v)
            for k, v in df.groupby("gender")["average score"].mean().sort_values(ascending=False).items()
        }
    if "parental level of education" in df.columns and "average score" in df.columns:
        group_insights["average_by_parental_education"] = {
            str(k): _round_float(v)
            for k, v in df.groupby("parental level of education")["average score"].mean().sort_values(ascending=False).items()
        }

    correlations: dict[str, float | None] = {}
    for left in existing_score_cols:
        for right in existing_score_cols:
            if left < right:
                correlations[f"{left} vs {right}"] = _round_float(
                    pd.to_numeric(df[left], errors="coerce").corr(pd.to_numeric(df[right], errors="coerce"))
                )

    summary: dict[str, Any] = {
        "file_name": path.name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "missing_required_columns": missing_required,
        "missing_values": {col: int(count) for col, count in df.isna().sum().items()},
        "duplicates": int(df.duplicated().sum()),
        "numeric_stats": numeric_stats,
        "top_values": top_values,
        "group_insights": group_insights,
        "correlations": correlations,
    }

    chart_path = str(output / "students_scores_chart.png")
    generate_student_chart(df, chart_path)

    json_path = output / "student_analysis_summary.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary, chart_path


def generate_student_chart(df: pd.DataFrame, output_path: str | Path) -> None:
    score_cols = [col for col in SCORE_COLUMNS if col in df.columns]
    if not score_cols:
        missing = df.isna().sum().sort_values(ascending=False).head(8)
        plt.figure(figsize=(10, 5))
        missing.plot(kind="bar")
        plt.title("Пропуски по столбцам")
        plt.xlabel("Столбцы")
        plt.ylabel("Количество пропусков")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    means = df[score_cols].apply(pd.to_numeric, errors="coerce").mean().sort_values(ascending=False)
    plt.figure(figsize=(9, 5))
    means.plot(kind="bar")
    plt.title("Средние баллы студентов")
    plt.xlabel("Предмет")
    plt.ylabel("Средний балл")
    plt.ylim(0, 100)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

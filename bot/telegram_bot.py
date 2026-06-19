from __future__ import annotations

import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from analysis.student_analysis import is_allowed_file, safe_filename
from llm.groq_client import GroqClient

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


class StudentAnalyticsBot:
    def __init__(self, token: str, llm: GroqClient, admin_id: int) -> None:
        self.token = token
        self.llm = llm
        self.admin_id = admin_id
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Отправь CSV или Excel-файл с датасетом StudentsPerformance.\n\n"
            "Я посчитаю метрики по math/reading/writing score, проверю качество данных, "
            "найду зависимости и пришлю график."
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Поддерживаемые форматы: .csv, .xlsx, .xls\n"
            "Максимальный размер файла: 10 МБ\n\n"
            "Ожидаемые столбцы: gender, race/ethnicity, parental level of education, lunch, "
            "test preparation course, math score, reading score, writing score."
        )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        document = message.document

        if document.file_size and document.file_size > MAX_FILE_SIZE_BYTES:
            await message.reply_text("Файл слишком большой. Максимальный размер: 10 МБ.")
            return

        if not is_allowed_file(document.file_name):
            await message.reply_text("Можно отправлять только .csv, .xlsx или .xls")
            return

        await message.reply_text("Файл получен. Анализирую датасет студентов...")

        with tempfile.TemporaryDirectory(prefix="students_dataset_") as tmp:
            tmp_dir = Path(tmp)
            local_path = tmp_dir / safe_filename(document.file_name)
            tg_file = await context.bot.get_file(document.file_id)
            await tg_file.download_to_drive(custom_path=str(local_path))

            try:
                report, chart_path = self.llm.run_student_agent(local_path, tmp_dir)
            except Exception as exc:
                await message.reply_text(f"Ошибка анализа: {exc}")
                return

            await message.reply_text(report)
            if chart_path and Path(chart_path).exists():
                await message.reply_photo(photo=chart_path, caption="График по датасету студентов")

    def run(self) -> None:
        self.app.run_polling()

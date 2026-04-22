import os
import time
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from google import genai


# ==========================================
# 1. Scanner layer (OOP inheritance)
# ==========================================

class BaseScanner:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.files_data = []

    def scan(self):
        raise NotImplementedError

    def get_content(self):
        return self.files_data


class ProjectStructureScanner(BaseScanner):
    """Scanner that maps the project tree so the AI can see the full file layout."""

    def scan(self):
        tree_str = "Project Directory Structure:\n"
        exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', 'migrations', 'staticfiles', 'media', '.idea'}

        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            level = root.replace(str(self.base_dir), '').count(os.sep)
            indent = ' ' * 4 * level
            tree_str += f"{indent}📂 {os.path.basename(root)}/\n"
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if f.endswith('.py') or f.endswith('.html') or f.endswith('.sh') or f.endswith('.md'):
                    tree_str += f"{subindent}📄 {f}\n"

        self.files_data.append({
            'name': 'PROJECT_TREE',
            'path': 'Directory Structure',
            'content': tree_str
        })
        return self


class DjangoCoreScanner(BaseScanner):
    def __init__(self, base_dir, app_name='core'):
        super().__init__(base_dir)
        self.app_dir = self.base_dir / app_name
        self.target_files = ['models.py', 'views_legacy.py', 'urls.py', 'forms.py']

    def scan(self):
        for file_name in self.target_files:
            file_path = self.app_dir / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.files_data.append({
                        'name': file_name,
                        'path': str(file_path.relative_to(self.base_dir)),
                        'content': f.read()
                    })
        return self


class SettingsScanner(BaseScanner):
    def scan(self):
        settings_path = self.base_dir / 'student_drive' / 'settings.py'
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                self.files_data.append({
                    'name': 'settings.py',
                    'path': 'student_drive/settings.py',
                    'content': f.read()
                })
        return self


# ==========================================
# 2. Presentation layer (documentation UI/UX)
# ==========================================

class MarkdownUXFormatter:
    @staticmethod
    def generate_ui(ai_analysis_text):
        template = f"""# 🚀 Student Drive - אינטליגנציה, ארכיטקטורה ומעקב

![Status](https://img.shields.io/badge/Status-Active-success)
![Security](https://img.shields.io/badge/Security_Scan-Passed-green)
![Architecture](https://img.shields.io/badge/Architecture-Mapped-purple)

> **תקציר מנהלים:** קובץ זה נוצר ומתוחזק אוטומטית על ידי סוכן ה-AI. הוא ממפה את עץ הפרויקט, מציג תמונת מצב ויזואלית, ביקורת קוד מקיפה, ורשימת משימות אופרטיבית.

---

## 📑 תוכן עניינים
1. [🌳 עץ הפרויקט ותפקידי הקבצים](#-1-עץ-הפרויקט-ותפקידי-הקבצים)
2. [📈 תמונת מצב וציון בריאות](#-2-תמונת-מצב-וציון-בריאות)
3. [🗺️ מפת ארכיטקטורה (Visual Flowchart)](#-3-מפת-ארכיטקטורה-visual-flowchart)
4. [💡 ביקורת קוד אדריכלית](#-4-ביקורת-קוד-אדריכלית-code-review)
5. [✅ צ'ק-ליסט משימות](#-5-צק-ליסט-משימות-action-items)

---

{ai_analysis_text}

---
*נבנה באהבה על ידי סוכן ה-AI שלך 🤖 | מופעל באמצעות Gemini 2.5 Flash*
"""
        return template


# ==========================================
# 3. Main command
# ==========================================

class Command(BaseCommand):
    help = 'Runs the Advanced AI agent to scan the project, build trees, generate flowcharts, and update PROJECT_MIRROR.md'

    PRIMARY_MODEL = 'gemini-2.5-pro'
    FALLBACK_MODEL = 'gemini-2.5-flash'
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 2

    def add_arguments(self, parser):
        parser.add_argument(
            '--debug-api',
            action='store_true',
            help='Run a focused API connectivity/model-init debug check for this agent only.'
        )

    @staticmethod
    def _is_503_high_demand_error(error_text):
        text = (error_text or '').lower()
        return (
            '503' in text
            or 'unavailable' in text
            or 'high demand' in text
            or 'currently experiencing high demand' in text
        )

    @staticmethod
    def _is_model_not_available_error(error_text):
        text = (error_text or '').lower()
        return (
            '404' in text
            or 'not_found' in text
            or 'is not found' in text
            or 'is not supported for generatecontent' in text
        )

    def _generate_with_retry_and_fallback(self, client, prompt):
        models_to_try = [self.PRIMARY_MODEL, self.FALLBACK_MODEL]
        last_error = None

        for model_name in models_to_try:
            backoff = self.INITIAL_BACKOFF_SECONDS

            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Model call succeeded with '{model_name}' (attempt {attempt})."
                        )
                    )
                    return response

                except Exception as exc:
                    last_error = exc
                    err_text = str(exc)
                    is_503 = self._is_503_high_demand_error(err_text)
                    is_model_not_available = self._is_model_not_available_error(err_text)

                    if is_503 and attempt < self.MAX_RETRIES:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ {model_name} attempt {attempt} failed with 503/high demand. "
                                f"Retrying in {backoff}s..."
                            )
                        )
                        time.sleep(backoff)
                        backoff *= 2
                        continue

                    if is_503 or is_model_not_available:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ {model_name} is unavailable after {attempt} attempts. "
                                "Trying fallback model..."
                            )
                        )
                        break

                    raise

        raise RuntimeError(
            f"Both primary ('{self.PRIMARY_MODEL}') and fallback ('{self.FALLBACK_MODEL}') "
            f"models failed. Last error: {last_error}"
        )

    def _run_focused_api_debug_test(self, client):
        self.stdout.write(self.style.NOTICE("🧪 Running focused API debug test for run_agent only..."))
        debug_prompt = "Reply with exactly: OK"

        try:
            debug_response = self._generate_with_retry_and_fallback(client, debug_prompt)
            debug_text = (getattr(debug_response, 'text', '') or '').strip()
            self.stdout.write(self.style.SUCCESS(f"🧪 Debug response text: {debug_text}"))
            return True
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"❌ Debug API test failed: {exc}"))
            return False

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("🤖 Advanced Agent starting deep project scan..."))

        # Collect project data, including the directory tree
        tree_scanner = ProjectStructureScanner(settings.BASE_DIR).scan()
        core_scanner = DjangoCoreScanner(settings.BASE_DIR).scan()
        settings_scanner = SettingsScanner(settings.BASE_DIR).scan()

        all_files = tree_scanner.get_content() + core_scanner.get_content() + settings_scanner.get_content()

        context_for_ai = "Here is the current state of the Django project:\n\n"
        for file in all_files:
            context_for_ai += f"### FILE: {file['path']} ###\n```python\n{file['content']}\n```\n\n"

        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR("❌ GEMINI_API_KEY is missing!"))
            return
        self.stdout.write(self.style.WARNING(f"🔑 DEBUG: Using API Key starting with: {str(api_key)[:15]}..."))

        try:
            client = genai.Client(api_key=api_key)

            if kwargs.get('debug_api'):
                self._run_focused_api_debug_test(client)
                return

            self.stdout.write(
                self.style.NOTICE("🧠 Generating Flowcharts, Trees and Deep Analysis... (This might take a minute)"))

            prompt = f"""
            You are an Elite Django Software Architect. Analyze the following project files and the project directory structure.

            Write your response entirely in HEBREW. Format in pure Markdown. Do not wrap the whole response in markdown blocks.

            Your response MUST include exactly these 5 sections in this order:

            ## 🌳 1. עץ הפרויקט ותפקידי הקבצים
            First, display the project tree layout using a markdown code block. 
            Then, provide a categorized list of the files (e.g., Configuration, Models, Views, Templates, Scripts). 
            For each file, explain its specific role, what it is responsible for, and how it inherits from or connects to other files (e.g., "views_legacy.py imports forms from forms.py and models from models.py to render the logic").

            ## 📈 2. תמונת מצב וציון בריאות
            Give a brief overview of the project state. Give a 'Health Score' out of 100 based on code cleanliness, security, and structure.

            ## 🗺️ 3. מפת ארכיטקטורה (Visual Flowchart)
            Create a Mermaid.js diagram (`mermaid` block) showing the core architecture. Use an `erDiagram` or `classDiagram` to show how the models relate to each other and their inheritances.

            ## 💡 4. ביקורת קוד אדריכלית (Code Review)
            Provide 3-5 high-level, actionable recommendations (Security, Performance, DRY).

            ## ✅ 5. צ'ק-ליסט משימות (Action Items)
            Create a markdown checklist (using - [ ]) of the top 3 most important technical tasks to fix or build next.

            Here are the project files and structure:
            {context_for_ai}
            """

            response = self._generate_with_retry_and_fallback(client, prompt)

            final_markdown = MarkdownUXFormatter.generate_ui(response.text)

            output_path = settings.BASE_DIR / 'PROJECT_MIRROR.md'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown)

            self.stdout.write(self.style.SUCCESS(f"🎉 SUCCESS! Advanced Architecture Map updated at: {output_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ AI Analysis failed: {str(e)}"))

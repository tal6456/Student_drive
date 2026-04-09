import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from google import genai


# ==========================================
# 1. שכבת הסורקים (OOP Inheritance)
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
    """סורק חדש: ממפה את עץ הפרויקט כדי שה-AI יכיר את כל הקבצים"""

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
# 2. שכבת העיצוב (Documentation UI/UX)
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
# 3. הפקודה הראשית (המוח המנצח המשודרג)
# ==========================================

class Command(BaseCommand):
    help = 'Runs the Advanced AI agent to scan the project, build trees, generate flowcharts, and update PROJECT_MIRROR.md'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("🤖 Advanced Agent starting deep project scan..."))

        # איסוף מידע כולל עץ הפרויקט
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

        self.stdout.write(
            self.style.NOTICE("🧠 Generating Flowcharts, Trees and Deep Analysis... (This might take a minute)"))

        try:
            client = genai.Client(api_key=api_key)

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
            prompt = f"""
            You are an Elite Django Software Architect. Analyze the following project files and the project directory structure.

            Write your response entirely in HEBREW. Format in pure Markdown. Do not wrap the whole response in markdown blocks.

            Your response MUST include exactly these 5 sections in this order:

            ## 🌳 1. עץ הפרויקט ותפקידי הקבצים
            First, display the project tree layout using a markdown code block. 
            Then, provide a categorized list of the files (e.g., Configuration, Models, Views). For each file, explain its specific role and how it connects to other files.

            ## 📈 2. תמונת מצב וציון בריאות
            Give a brief overview of the project state. Give a 'Health Score' out of 100 based on code cleanliness, security, and structure.

            ## 🗺️ 3. מפת ארכיטקטורה (Visual Flowchart)
            Create a Mermaid.js diagram (`mermaid` block) showing the core architecture. 
            CRITICAL INSTRUCTION FOR MERMAID: You MUST use a very simple `classDiagram`. 
            Do NOT use `erDiagram` or complex relationship syntax that might cause syntax errors. 
            Just show the main models (CustomUser, Course, Document, Post, etc.) and basic arrows (-->) for their relationships. Keep it safe and simple.

            ## 💡 4. ביקורת קוד אדריכלית (Code Review)
            Provide 3-5 actionable recommendations strictly divided by urgency using these exact emojis and categories:
            * 🔴 קריטי (Security/Bugs) - סכנות אבטחה, קריסות אפשריות או שגיאות לוגיות חמורות.
            * 🟡 שיפור ביצועים (Optimization) - עומס על מסד הנתונים (N+1 queries), זמני טעינה איטיים.
            * 🟢 ניקיון קוד (Clean Code / DRY) - חוב טכני, מניעת כפילויות, ארגון קוד.

            ## ✅ 5. צ'ק-ליסט משימות (Action Items)
            Create a markdown checklist (using - [ ]) of the top 3 most important technical tasks to fix or build next, based primarily on the 🔴 Critical and 🟡 Optimization findings.

            Here are the project files and structure:
            {context_for_ai}
            """

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )

            final_markdown = MarkdownUXFormatter.generate_ui(response.text)

            output_path = settings.BASE_DIR / 'PROJECT_MIRROR.md'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown)

            self.stdout.write(self.style.SUCCESS(f"🎉 SUCCESS! Advanced Architecture Map updated at: {output_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ AI Analysis failed: {str(e)}"))
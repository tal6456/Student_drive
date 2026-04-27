# 🚀 Student Drive - אינטליגנציה, ארכיטקטורה ומעקב

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

## 🌳 1. עץ הפרויקט ותפקידי הקבצים

```
📂 student_drive/
    📄 build.sh
    📄 import_courses.py
    📄 manage.py
    📄 PROJECT_MIRROR.md
    📄 QA_REPORT_LOG.md
    📂 core/
        📄 adapters.py
        📄 admin.py
        📄 agent_brain.py
        📄 agent_views.py
        📄 ai_utils.py
        📄 apps.py
        📄 context_processors.py
        📄 forms.py
        📄 middleware.py
        📄 models.py
        📄 personal_drive.py
        📄 signals.py
        📄 student_agent.py
        📄 utils.py
        📄 __init__.py
        📂 management/
            📄 __init__.py
            📂 commands/
                📄 run_agent.py
                📄 seed_academic_data.py
                📄 __init__.py
        📂 static/
            📂 core/
                📂 css/
                📂 js/
            📂 css/
            📂 js/
            📂 ישן/
        📂 templates/
            📄 404.html
            📄 500.html
            📂 account/
                📄 email_confirm.html
                📄 login.html
                📄 logout.html
                📄 password_change.html
                📄 password_reset.html
                📄 password_reset_done.html
                📄 password_reset_from_key.html
                📄 password_reset_from_key_done.html
                📄 signup.html
                📄 verification_sent.html
            📂 core/
                📄 accessibility.html
                📄 add_course.html
                📄 agent_report.html
                📄 agent_widget.html
                📄 analytics.html
                📄 base.html
                📄 change_password.html
                📄 chat_room.html
                📄 chat_room_enhanced.html
                📄 community_card_item.html
                📄 community_feed.html
                📄 complete_profile.html
                📄 course_detail.html
                📄 discover_communities.html
                📄 document_viewer.html
                📄 donations.html
                📄 feedback.html
                📄 files_tinder.html
                📄 friends_list.html
                📄 home.html
                📄 lecturers_index.html
                📄 login.html
                📄 notifications_list.html
                📄 personal_drive.html
                📄 privacy.html
                📄 profile.html
                📄 public_profile.html
                📄 register.html
                📄 search_results.html
                📄 settings.html
                📄 share_target_finish.html
                📄 social_base.html
                📄 staff_detail.html
                📄 terms.html
                📄 wallet.html
                📄 _search_form.html
                📂 partials/
                    📄 alert_banner.html
                    📄 base_body_top.html
                    📄 base_footer.html
                    📄 base_scripts.html
                    📄 base_styles.html
                    📄 collapsible_semester.html
                    📄 comment_item.html
                    📄 community_sidebar.html
                    📄 course_row.html
                    📄 doc_row.html
                    📄 file_grid_card.html
                    📄 post_card.html
                    📄 share_modal.html
                    📄 sorting_toolbar.html
            📂 socialaccount/
                📄 login.html
                📄 signup.html
        📂 tests/
            📄 base.py
            📄 test_a11y_widget.py
            📄 test_economy.py
            📄 test_files_tinder.py
            📄 test_integration.py
            📄 test_models.py
            📄 test_security_regressions.py
            📄 test_utils.py
            📄 test_views.py
            📄 __init__.py
        📂 views/
            📄 academic.py
            📄 accounts.py
            📄 api.py
            📄 documents.py
            📄 friends_chat.py
            📄 pages.py
            📄 social.py
            📄 __init__.py
    📂 documents/
    📂 locale/
        📂 en/
            📂 LC_MESSAGES/
    📂 student_drive/
        📄 asgi.py
        📄 settings.py
        📄 urls.py
        📄 wsgi.py
    📂 templates/
        📂 admin/
            📄 base_site.html
```

**תפקידי הקבצים:**

**1. קבצי מערכת ו-Configuration:**
*   `student_drive/manage.py`: כלי שורת הפקודה של Django. אחראי להפעלת שרת הפיתוח, ביצוע מיגרציות ועוד. הוא מהווה את נקודת הכניסה הניהולית לפרויקט.
*   `student_drive/settings.py`: קובץ ההגדרות הראשי של הפרויקט. מוגדרות בו בסיס הנתונים, יישומים מותקנים, הגדרות אבטחה, שרת מייל (Gmail), שילוב Allauth, והגדרות Amazon S3 לאחסון קבצים. הוא מחבר את כל רכיבי המערכת יחד ומשפיע על יציבותה וביצועיה.
*   `student_drive/urls.py`: הגדרות הניתוב (URL routing) הראשיות של הפרויקט. מפנה בקשות נכנסות (HTTP requests) ל-`core.urls` (לא סופק אבל מניח שקיים) ומטפל גם בניתובים ברמת הפרויקט כמו Admin.
*   `student_drive/wsgi.py`: נקודת כניסה לשרתי WSGI (Web Server Gateway Interface) המטפלים בבקשות HTTP בסביבת Production.
*   `student_drive/asgi.py`: נקודת כניסה לשרתי ASGI (Asynchronous Server Gateway Interface) המאפשרים טיפול בבקשות אסינכרוניות (למשל, WebSockets).
*   `core/apps.py`: הגדרות היישום (App) `core`. מנהל את קונפיגורציית ה-App, למשל הגדרת שמו.
*   `core/middleware.py`: מכיל את `ProfileCompletionMiddleware` שמטרתו להפנות משתמשים חדשים לדף השלמת פרופיל לאחר הרשמה או התחברות ראשונה. הוא פועל בכל בקשת HTTP. מתחבר ל-`core.models.UserProfile` כדי לבדוק את מצב הפרופיל.
*   `core/adapters.py`: מרחיב את התנהגות Allauth (מערכת ההרשמה והאימות) כדי להתאים אותה לצרכי הפרויקט, למשל ניתוב לאחר התחברות או הרשמה. יורש מה-Adapters של Allauth.
*   `core/context_processors.py`: מספק משתנים גלובליים לכל התבניות (templates) באתר. הוא מאפשר גישה מהירה לנתונים כמו מספר התראות שלא נקראו (`Notification` מ-`core.models`) בכל דף.

**2. מודלים (Models):**
*   `core/models.py`: קובץ זה הוא ליבת המידע של המערכת. הוא מגדיר את כל מודלי הנתונים (כגון `CustomUser`, `UserProfile`, `University`, `Course`, `Document`, `Post`, `AgentKnowledge`, `Notification`, `CoinTransaction`, `ChatRoom` ועוד), את השדות שלהם, הקשרים ביניהם (ForeignKey, ManyToMany) והלוגיקה הפנימית שלהם (כמו `save` שמפעיל דחיסת תמונות או משיכת טקסט). קובץ זה מיובא כמעט על ידי כל קובץ פייתון אחר בפרויקט המקיים אינטראקציה עם בסיס הנתונים. כולל גם את `signals` כחלק מהמחלקה.
    *   **דוגמה לחיבור:** `UserProfile` מקושר ל-`CustomUser` באמצעות `OneToOneField`, וכן ל-`University` ול-`Major` באמצעות `ForeignKey`. שינויים בו דורשים `makemigrations` ו-`migrate`.

**3. Views ו-Logic:**
*   `core/views/__init__.py`: קובץ איחוד שמייבא את כל פונקציות ה-view מתתי הקבצים בתיקיית `views`. מאפשר ל-`urls.py` להפנות בקלות לכל ה-views מבלי לייבא כל קובץ בנפרד.
*   `core/views/academic.py`: מכיל views לניהול אקדמי: דף הבית, חיפוש קורסים, פרטי קורס, ניהול תיקיות בתוך קורסים, דירוג מרצים ועוד. משתמש במודלים כמו `Course`, `Folder`, `Document`, `AcademicStaff` מ-`core.models` ובטפסים מ-`core.forms`.
*   `core/views/documents.py`: מטפל במחזור החיים של מסמכים: העלאה (כולל שיתוף מהמערכת), הורדה מאובטחת, תצוגה מקדימה, סיכום אוטומטי (AI), לייקים ודיווחים על קבצים. עושה שימוש נרחב ב-`Document` ו-`DownloadLog` מ-`core.models`, ובפונקציות עזר מ-`core.ai_utils` ו-`core.utils`.
*   `core/views/accounts.py`: מרכז את ה-views הקשורים לחשבון המשתמש: פרופיל אישי, הגדרות, השלמת פרופיל, שינוי סיסמה, מחיקת חשבון, רשימת התראות וארנק המטבעות. משתמש ב-`UserProfile`, `Document`, `DownloadLog`, `Notification` מ-`core.models` ובטפסים מ-`core.forms`.
*   `core/views/social.py`: מנהל את הפיד החברתי והקהילות: הצגת פוסטים, יצירת פוסטים (רגילים, מכירה, וידאו), תגובות ולייקים בקהילות. מתחבר למודלים `Community`, `Post`, `MarketplacePost`, `VideoPost`, `Comment` מ-`core.models`.
*   `core/views/friends_chat.py`: מטפל בפיצ'רים חברתיים כמו פרופילים ציבוריים, בקשות חברות, רשימת חברים וחדרי צ'אט עם אפשרות לצרף קבצים. משתמש ב-`Friendship`, `Notification`, `ChatRoom`, `ChatMessage` מ-`core.models`.
*   `core/views/api.py`: מספק נקודות קצה (AJAX endpoints) לביצוע פעולות מהירות מה-Frontend ללא רענון דף, כמו טעינת מסלולי לימוד, הוספת אוניברסיטאות/מסלולים, ומחיקת פריטים. עושה שימוש נרחב במודלים כמו `University`, `Major`, `Document`, `Folder` מ-`core.models` וב-`check_deletion_permission` מ-`core.utils`.
*   `core/views/pages.py`: מכיל views לדפי מידע כלליים כמו תנאי שימוש, תרומות, נגישות, פרטיות, דף משוב (Feedback) ולוח מחוונים (Dashboard) אנליטי. משתמש במודלים כמו `Document`, `Course`, `UserProfile`, `Report`, `Feedback`, `Notification` מ-`core.models`. *יש כפילות עם `notifications_list` מ-`accounts.py`.*
*   `core/personal_drive.py`: מכיל views ספציפיים לניהול הדרייב האישי של המשתמש (קבצים שהועלו, היסטוריית הורדות, קבצים מועדפים). קובץ זה הוא view אך אינו ממוקם בתיקיית `core/views/`, מהווה חוסר עקביות. מיובא אליו `Document`, `DownloadLog`, `Vote`, `ExternalResource` מ-`core.models`.

**4. AI ו-Agent:**
*   `core/agent_brain.py`: ליבת המוח של סוכן ה-AI. ככל הנראה מנהל את האינטגרציה עם Gemini API (מוזכר ב-`settings.py`) לביצוע פעולות כמו מיצוי טקסט וסיכום. מיובא אליו `StudentAgentBrain` מ-`agent_brain.py` (הצהרה עצמית?) ומודלי `AgentKnowledge`, `Course` מ-`core.models`.
*   `core/agent_views.py`: Views המאפשרים אינטראקציה עם סוכן ה-AI באמצעות בקשות AJAX (למשל, העלאת קבצים ללמידה ושאילת שאלות). משתמש ב-`agent_brain.py` וב-`AgentKnowledge`, `Course` מ-`core.models`.
*   `core/ai_utils.py`: קובץ שנועד כנראה לעזרים ספציפיים ל-AI. ייתכן שיש חפיפה או חוסר שימוש בו בהינתן `agent_brain.py` ו-`core/utils.py` שמבצע משיכת טקסט.
*   `core/student_agent.py`: נראה שזהו קובץ נוסף הקשור לסוכן ה-AI. יש לבדוק אם הוא משלים את `agent_brain.py` או מהווה כפילות/גרסה ישנה.

**5. Utilities ו-Helpers:**
*   `core/utils.py`: קובץ עזר רחב המכיל פונקציות שימושיות כלליות: דחיסת תמונות ל-WebP, ולידציה לגודל וסוג קבצים (כולל "Magic Numbers" לאבטחה), מנגנון בדיקת הרשאות מחיקה חכם, משיכת טקסט מקובצי PDF ו-DOCX, קבלת כתובת IP של לקוח, שליחת התראות, ומנגנון עיבוד טרנזקציות מטבעות (Coins). קובץ זה מיובא על ידי מספר רב של views, models ו-signals.
*   `core/signals.py`: מכיל פונקציות שמגיבות לאירועים ספציפיים במערכת (Django Signals). לדוגמה, `notify_students_on_new_file` שולח התראות לסטודנטים כשקובץ חדש מועלה לקורס מועדף. `grant_daily_login_bonus` מעניק מטבעות על התחברות יומית. מתחבר ל-`core.models`, `core.utils`.

**6. טפסים (Forms):**
*   `core/forms.py`: מכיל את הגדרות הטפסים של Django (כגון `CourseForm`, `UserProfileForm`, `CustomSignupForm`) המאפשרים אינטראקציה עם המודלים מ-`core.models` דרך ממשק משתמש.

**7. Admin:**
*   `core/admin.py`: רושם את מודלי הנתונים (מ-`core.models`) לממשק הניהול של Django, מה שמאפשר למנהלים לנהל את נתוני המערכת.

**8. קבצי סטטיק ותבניות (Static & Templates):**
*   `core/static/`: מכיל קבצי CSS ו-JS ספציפיים ליישום `core`.
*   `core/templates/core/`: מכיל את קבצי ה-HTML (תבניות) הספציפיים ליישום `core`.
*   `student_drive/templates/`: מכיל תבניות כלל-פרויקטליות (כמו התבניות של Allauth ותבניות ה-admin המותאמות אישית).
*   `core/templates/account/`, `core/templates/socialaccount/`: תבניות מותאמות אישית של Allauth עבור תהליכי הרשמה, התחברות, איפוס סיסמה וכו'.

**9. Scripts ותיעוד:**
*   `build.sh`: סקריפט Shell לבנייה או פריסת הפרויקט.
*   `import_courses.py`: סקריפט Python לייבוא נתוני קורסים.
*   `PROJECT_MIRROR.md`, `QA_REPORT_LOG.md`: קבצי תיעוד ויומני דיווח QA.
*   `locale/en/LC_MESSAGES/`: קבצי תרגום עבור בינאום (Internationalization), במקרה זה לאנגלית.

**10. בדיקות (Tests):**
*   `core/tests/`: תיקייה המכילה קבצי בדיקה (unit tests, integration tests) לבדיקת תקינות הקוד עבור מודלים, views, אבטחה, נגישות ועוד.

## 📈 2. תמונת מצב וציון בריאות

**סקירה כללית על מצב הפרויקט:**
הפרויקט "Student Drive" הוא יישום Django עשיר בפיצ'רים, מקיף ומתוכנן היטב בבסיסו. הוא מציע פלטפורמה אקדמית-חברתית מלאה הכוללת ניהול קורסים ומסמכים, מערכת קהילתית מובנית (פיד חברתי, צ'אט), מנגנוני גיימיפיקציה (מטבעות, דירוגים), סוכן AI אישי, ומערכת אימות משתמשים חזקה באמצעות Allauth (כולל אימות מייל והתחברות עם גוגל). הפרויקט מראה מודעות גבוהה לאבטחת מידע (ולידציות קבצים, HSTS, סיסמאות חזקות) ולביצועים (דחיסת תמונות, `select_related`/`prefetch_related`). חלוקת ה-views למודולים שונים (academic, documents, social, friends\_chat וכו') היא צעד מצוין לשמירה על סדר ומופרדות אחריות (Separation of Concerns).

עם זאת, קיימים מספר "חורים" בארכיטקטורה וביישום שיכולים להשפיע על תחזוקה עתידית וסקיילביליות. קובץ ה-`models.py` גדול באופן חריג ומרכז את כל הגדרות המודלים, מה שמקשה על ניהול. קיימת אי-עקביות במיקום קבצי views (למשל `personal_drive.py` מחוץ לתיקיית `views/`), וכפילות ביישום views מסוימים (`notifications_list`). הטיפול בשגיאות בסוכן ה-AI ובמנגנון ההתראות יכול להיות מפורט ועמיד יותר.

**ציון בריאות (מתוך 100): 75/100**

*   **ניקיון קוד (Code Cleanliness):** **70/100**
    *   **חוזקות:** חלוקה טובה של ה-views לקבצים מודולריים, שימוש בפונקציות עזר, שימוש ב-`select_related` ו-`prefetch_related` לביצועים. קבצי Templates נראים מסודרים.
    *   **חולשות:** קובץ `core/models.py` עצום ומורכב (God Object), קובץ `core/utils.py` הפך ל-"ארגז כלים" גדול מדי. כפילות ב-`notifications_list` ב-`core/views/accounts.py` ו-`core/views/pages.py`. קיום קבצי `ai_utils.py` ו-`student_agent.py` לצד `agent_brain.py` מעיד על חוסר ניקיון או כפילות בתחום ה-AI.
*   **אבטחה (Security):** **80/100**
    *   **חוזקות:** שימוש ב-`AbstractUser` מותאם אישית, ולידציית קבצים קפדנית (גודל, סוג באמצעות "Magic Numbers"), דחיסת תמונות, שימוש ב-`Password_Hashers` חזקים, הגדרות CSRF/XSS, ו-HSTS ב-Production. טיפול בהפניות (Referral) בצורה סבירה. שימוש ב-`login_required` כמעט בכל ה-views הרלוונטיים.
    *   **חולשות:** `CSRF_COOKIE_HTTPONLY = True` בהגדרות יכול להקשות על בקשות AJAX ללא טיפול מפורש (קריאת טוקן מ-DOM). טיפול כללי מדי ב-`except Exception as e` ב-`agent_views.py` ובמקומות אחרים עלול להסתיר פרצות או וקטורי תקיפה (לוגים מפורטים עדיפים). הדפסת שגיאות של התראות במקום לוג/טיפול חזק יותר ב-`process_transaction` עלולה להסתיר בעיות (אם כי הרעיון לא להפיל טרנזקציה על התראה הוא הגיוני).
*   **מבנה (Structure):** **75/100**
    *   **חוזקות:** חלוקה טובה של ה-views לחבילות (`core/views/`) היא מודל ארכיטקטוני חזק. שימוש ב-`__init__.py` לייבוא מאפשר ניתוב נקי. קיימת הפרדה בין קבצי פרויקט וקבצי App. שימוש בקונבנציות Django סטנדרטיות (templates, static, admin).
    *   **חולשות:** קובץ `core/models.py` הוא נקודת תורפה מבנית קריטית – יש לפצלו. קובץ `core/personal_drive.py` ממוקם מחוץ לתיקיית ה-views, מה שפוגע בעקביות המבנית. קיומן של מספר קבצי עזר ל-AI באותה תיקייה מעיד על חוסר ארגון פוטנציאלי.

**לסיכום:** הפרויקט בעל פוטנציאל גבוה ועם בסיס טכנולוגי חזק. הליטושים והשינויים המבניים המומלצים ישפרו משמעותית את קלות התחזוקה, הסקיילביליות והאיתנות שלו לטווח הארוך.

## 🗺️ 3. מפת ארכיטקטורה (Visual Flowchart)

```mermaid
erDiagram
    CustomUser {
        int id PK
        string username
        string email
        string role
    }
    UserProfile {
        int id PK
        int user_id FK
        int university_id FK
        int major_id FK
        int current_balance
        int lifetime_coins
        string profile_picture
        string referral_code
    }
    Friendship {
        int id PK
        int user_from_id FK
        int user_to_id FK
        string status
    }
    University {
        int id PK
        string name
        string brand_color
    }
    Major {
        int id PK
        int university_id FK
        string name
    }
    Course {
        int id PK
        int major_id FK
        int creator_id FK
        string name
        int year
        string semester
        int view_count
    }
    Folder {
        int id PK
        int course_id FK
        int parent_id FK
        int created_by_id FK
        string name
        string color
    }
    Document {
        int id PK
        int course_id FK
        int folder_id FK
        int uploaded_by_id FK
        string title
        string file
        string file_content
        int download_count
    }
    ExternalResource {
        int id PK
        int user_id FK
        string title
        string link
        string file
    }
    Post {
        int id PK
        int user_id FK
        int community_id FK
        string content
        datetime created_at
    }
    MarketplacePost {
        int post_ptr_id PK, FK
        decimal price
        string category
    }
    VideoPost {
        int post_ptr_id PK, FK
        string youtube_url
        string thumbnail
    }
    Comment {
        int id PK
        int post_id FK
        int user_id FK
        string text
    }
    AcademicStaff {
        int id PK
        int university_id FK
        int created_by_id FK
        string name
        float average_rating
    }
    Lecturer {
        int academicstaff_ptr_id PK, FK
        string title
    }
    TeachingAssistant {
        int academicstaff_ptr_id PK, FK
        string title
    }
    StaffReview {
        int id PK
        int staff_member_id FK
        int user_id FK
        int rating
        string review_text
    }
    Community {
        int id PK
        int university_id FK
        int major_id FK
        string name
        string community_type
    }
    AgentKnowledge {
        int id PK
        int owner_id FK
        string file
        string extracted_text
        string course_name
    }
    Notification {
        int id PK
        int user_id FK
        int sender_id FK
        string notification_type
        string title
        string message
        string link
        int content_type_id FK
        int object_id
    }
    CoinTransaction {
        int id PK
        int user_id FK
        int actor_id FK
        int amount
        string transaction_type
        string description
    }
    UserCourseSelection {
        int id PK
        int user_id FK
        int course_id FK
        bool is_starred
    }
    ChatRoom {
        int id PK
        datetime created_at
    }
    ChatMessage {
        int id PK
        int room_id FK
        int sender_id FK
        string content
        int attached_file_id FK
        datetime timestamp
    }
    DownloadLog {
        int id PK
        int user_id FK
        int document_id FK
    }
    Vote {
        int id PK
        int user_id FK
        int document_id FK
        int value
    }
    DocumentComment {
        int id PK
        int document_id FK
        int user_id FK
        string text
    }
    Report {
        int id PK
        int document_id FK
        int user_id FK
        string reason
    }
    Feedback {
        int id PK
        int user_id FK
        string subject
        string message
        string screenshot
    }
    CourseSemesterStaff {
        int id PK
        int course_id FK
        int staff_member_id FK
        int academic_year
        string semester
    }

    CustomUser ||--o{ UserProfile : has
    CustomUser ||--o{ Friendship : sends/receives
    CustomUser ||--o{ Post : creates
    CustomUser ||--o{ Comment : creates
    CustomUser ||--o{ Document : uploads
    CustomUser ||--o{ Report : reports
    CustomUser ||--o{ StaffReview : reviews
    CustomUser ||--o{ Feedback : submits
    CustomUser ||--o{ AgentKnowledge : owns
    CustomUser ||--o{ Notification : receives
    CustomUser ||--o{ CoinTransaction : performs
    CustomUser ||--o{ UserCourseSelection : selects
    CustomUser ||--o{ ChatRoom : participates
    CustomUser ||--o{ ChatMessage : sends
    CustomUser ||--o{ DownloadLog : downloads
    CustomUser ||--o{ Vote : votes
    CustomUser ||--o{ DocumentComment : comments
    CustomUser ||--o{ ExternalResource : owns

    UserProfile }o--|| University : attends
    UserProfile }o--|| Major : studies
    UserProfile }o--o{ Course : favorites

    University ||--o{ Major : has
    University ||--o{ AcademicStaff : employs
    University ||--o{ Community : forms

    Major ||--o{ Course : offers

    Course ||--o{ Folder : contains
    Course ||--o{ Document : contains
    Course ||--o{ CourseSemesterStaff : has_staff
    Course ||--o{ UserCourseSelection : selected_by

    Folder ||--o{ Document : contains
    Folder }o--o| AcademicStaff : assigned_to

    Document ||--o{ Report : is_reported
    Document ||--o{ DownloadLog : is_downloaded
    Document ||--o{ Vote : is_voted_on
    Document ||--o{ DocumentComment : has_comments
    Document ||--o{ ChatMessage : attached_to

    Post ||--o{ Comment : has_comments
    Post ||--o{ MarketplacePost : is_a
    Post ||--o{ VideoPost : is_a
    Post }o--|| Community : posted_in
    Post }o--o{ CustomUser : liked_by

    AcademicStaff <|-- Lecturer : is_a
    AcademicStaff <|-- TeachingAssistant : is_a
    AcademicStaff ||--o{ StaffReview : receives
    AcademicStaff ||--o{ CourseSemesterStaff : assigned_to

    Community }o--o{ CustomUser : has_members
    Community ||--o{ Post : contains

    ChatRoom ||--o{ ChatMessage : contains
    ChatRoom }o--o{ CustomUser : has_participants

    Notification }o--|| CustomUser : for
    Notification }o--o{ ContentType : targets_object (GenericFK)

    CoinTransaction }o--|| CustomUser : for
```

## 💡 4. ביקורת קוד אדריכלית (Code Review)

להלן 3 המלצות אדריכליות ברמה גבוהה לשיפור הפרויקט:

1.  **פיצול מודלים (DRY & Maintainability):**
    *   **המלצה:** קובץ `core/models.py` הוא גדול באופן דרמטי (מעל 500 שורות קוד וכ-30 מודלים). זוהי חולשה ארכיטקטונית מרכזית שפוגעת בקריאות, בתחזוקה ובסקיילביליות. קובץ כה גדול מקשה על איתור באגים, עבודה בצוות (Merge Conflicts) וניהול התלותיות.
    *   **פעולה נדרשת:** פצל את `core/models.py` למספר קבצים קטנים יותר, לפי תחומים לוגיים. לדוגמה:
        *   `core/models/users.py` (עבור `CustomUser`, `UserProfile`, `Friendship`)
        *   `core/models/academic.py` (עבור `University`, `Major`, `Course`, `Folder`, `AcademicStaff`)
        *   `core/models/documents.py` (עבור `Document`, `DownloadLog`, `ExternalResource`, `Vote`, `DocumentComment`)
        *   `core/models/community.py` (עבור `Community`, `Post`, `Comment`, `MarketplacePost`, `VideoPost`)
        *   `core/models/ai_agent.py` (עבור `AgentKnowledge`)
        *   `core/models/economy.py` (עבור `CoinTransaction`)
        *   `core/models/notifications.py` (עבור `Notification`, `Report`, `Feedback`)
        *   צור קובץ `core/models/__init__.py` שיאחד את כולם באמצעות ייבוא `from .users import *` וכך הלאה, כדי לשמר תאימות לאחור עם ייבוא `from core.models import ...`.

2.  **עיבוד אסינכרוני למשימות כבדות (Performance & Scalability):**
    *   **המלצה:** הפונקציות `extract_text_from_pdf` ו-`extract_text_from_docx` ב-`core/utils.py` נקראות מתוך מתודת `save()` של המודל `Document` (ב-`core/models.py`). משיכת טקסט מקבצים גדולים (PDF/DOCX) היא פעולה חוסמת ודורשת משאבי מעבד, והיא תאט באופן משמעותי את תהליך העלאת הקבצים ותפגע בחווית המשתמש.
    *   **פעולה נדרשת:** הטמע מערכת עיבוד אסינכרונית (כגון Celery עם Redis או RabbitMQ כ-Broker). העבר את משימות מיצוי הטקסט ואולי גם את דחיסת התמונות (אם היא חוסמת בקבצים גדולים) לתורי משימות אסינכרוניות. כשהמשתמש מעלה קובץ, השמירה הראשונית תתבצע מהר, והטקסט המחולץ יתווסף למודל ברקע לאחר שהמשימה תושלם. הדבר ישפר באופן דרמטי את responsiveness של המערכת.

3.  **אבטחת API וטיפול שגיאות מפורט (Security & Robustness):**
    *   **המלצה:** ה-views ב-`core/agent_views.py` וב-`core/views/api.py` מסתמכים על `login_required` לאימות, אך טיפול השגיאות בהם לעיתים גנרי מדי (לדוגמה: `except Exception as e` ב-`ask_agent_question`). בפרט, ההגדרה `CSRF_COOKIE_HTTPONLY = True` ב-`settings.py` יכולה לפגוע באבטחת ה-API עבור בקשות AJAX ולגרום לבעיות CSRF.
    *   **פעולה נדרשת:**
        *   **טיפול שגיאות:** החלף את בלוקי `except Exception as e` כלליים בטיפול שגיאות ספציפי יותר, ולוג את השגיאות המלאות למערכת לוגים חיצונית (כגון Sentry) במקום להדפיס לקונסול או להציג הודעה גנרית למשתמש. זה יאפשר ניטור ובקרה טובים יותר של בעיות ב-Production.
        *   **CSRF:** בדוק את השלכות `CSRF_COOKIE_HTTPONLY = True`. הגדרה זו מונעת מ-JavaScript לגשת לקוקי ה-CSRF. אם יש קריאות AJAX שדורשות גישה לטוקן מ-JS, יש לשנות זאת ל-`False` (כברירת מחדל של Django) או להבטיח שהטוקן מועבר באופן אחר (למשל, מטא-תג ב-HTML).
        *   **תיעוד API:** תיעד את ה-endpoints ב-`api.py` וב-`agent_views.py` כדי להבטיח שימוש נכון ובטוח בהם.

## ✅ 5. צ'ק-ליסט משימות (Action Items)

להלן 3 המשימות הטכניות החשובות ביותר לתיקון או בנייה בהמשך:

- [ ] **1. פיצול קובץ `core/models.py`:** פצל את קובץ המודלים העצום למספר קבצים קטנים יותר לפי תחומים לוגיים, וצור קובץ `__init__.py` בתיקיית `core/models/` כדי לאחד אותם. (תיאור מפורט בסעיף 4, המלצה 1).
- [ ] **2. הטמעת Celery למשימות אסינכרוניות:** הגדר Celery (או כלי דומה) ו-Redis/RabbitMQ, והעבר את משימות מיצוי הטקסט (מ-PDF/DOCX) מתוך `Document.save()` למשימות רקע אסינכרוניות. (תיאור מפורט בסעיף 4, המלצה 2).
- [ ] **3. איחוד views ותיקון מיקום `personal_drive.py`:**
    *   העבר את `core/personal_drive.py` לתוך `core/views/personal_drive.py` כדי לשמור על עקביות מבנית.
    *   אחד את שני ה-views של `notifications_list` (הקיימים ב-`core/views/accounts.py` וב-`core/views/pages.py`) ל-view יחיד ב-`core/views/accounts.py` ועדכן את הניתובים בהתאם. (תיאור מפורט בסעיף 2).

---
*נבנה באהבה על ידי סוכן ה-AI שלך 🤖 | מופעל באמצעות Gemini 2.5 Flash*

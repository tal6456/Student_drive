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
Project Directory Structure:
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
        📄 tasks.py
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
    📂 sent_emails/
    📂 student_drive/
        📄 asgi.py
        📄 celery.py
        📄 settings.py
        📄 urls.py
        📄 wsgi.py
        📄 __init__.py
    📂 templates/
        📂 admin/
            📄 base_site.html
```

**רשימת קבצים ותפקידיהם:**

*   **קונפיגורציה ושורש פרויקט (`student_drive/`)**:
    *   `build.sh`: סקריפט אוטומציה לבנייה/פריסה של הפרויקט. (לא סופק תוכן, אך תפקידו סטנדרטי)
    *   `import_courses.py`: סקריפט להזנת נתוני קורסים ראשוניים (לרוב נתונים לדוגמה או העברת נתונים).
    *   `manage.py`: כלי שורת הפקודה של Django לביצוע משימות ניהוליות (server run, migrations, etc.).
    *   `PROJECT_MIRROR.md`: קובץ Markdown המתעד את מבנה הפרויקט (מראה שקיים תיעוד למפתחים).
    *   `QA_REPORT_LOG.md`: קובץ Markdown לתיעוד דיווחי QA (מצביע על תהליכי בדיקה).
    *   `student_drive/asgi.py`: נקודת כניסה ליישומים אסינכרוניים (ASGI), משמש ל-WebSocket ו-Celery.
    *   `student_drive/celery.py`: קונפיגורציה של Celery, מערכת לתזמון והרצת משימות רקע (לדוגמה, עיבוד קבצים).
    *   `student_drive/settings.py`: הגדרות הליבה של פרויקט Django. מחבר את כל רכיבי המערכת, כולל מסד נתונים, שרתי אימייל, אחסון בענן (S3), אבטחה, אימות משתמשים (Allauth), ואינטגרציה עם Google API. הוא מייבא את `core.adapters` ו-`core.middleware` ומגדיר את `AUTH_USER_MODEL` ל-`core.CustomUser`.
    *   `student_drive/urls.py`: מפות ה-URL הראשיות של הפרויקט. מנתב בקשות ל-`core.urls` (לא סופק) ולמסלולי Allauth.
    *   `student_drive/wsgi.py`: נקודת כניסה ליישומים סינכרוניים (WSGI), משמש לשרתי ווב רגילים כמו Gunicorn.
*   **אפליקציית הליבה (`core/`)**:
    *   `core/adapters.py`: מכיל מחלקות Adapter עבור `allauth`, בעיקר לטיפול מותאם אישית בתהליכי הרשמה וחיבור (CustomSocialAccountAdapter) ולהפניה לדף השלמת פרופיל.
    *   `core/admin.py`: קונפיגורציה לממשק הניהול של Django. מגדיר כיצד מודלים ספציפיים (כמו `CustomUser` ו-`UserProfile`) מוצגים וניתנים לניהול ע"י מנהלי המערכת.
    *   `core/agent_brain.py`: (לא סופק תוכן) קוד הליבה המנהל את הלוגיקה של סוכן ה-AI, כנראה מתממשק למודלים של AI חיצוניים.
    *   `core/agent_views.py`: Views המטפלים באינטראקציות עם סוכן ה-AI. קולט קבצים (upload_agent_file) ושאלות משתמשים (ask_agent_question). מייבא מודלים כמו `AgentKnowledge` ו-`Course` ומפעיל את `StudentAgentBrain` מ-`agent_brain.py`.
    *   `core/ai_utils.py`: (לא סופק תוכן) כלי עזר כלליים הקשורים לבינה מלאכותית, כמו פונקציות לסיכום טקסט. `summarize_document_ai` ב-`documents.py` משתמש בה.
    *   `core/apps.py`: קונפיגורציה עבור אפליקציית ה-`core`, כולל הגדרת שם האפליקציה וטעינת Signals.
    *   `core/context_processors.py`: (לא סופק תוכן) מספק מידע גלובלי לכל הטמפלייטים (לדוגמה, ספירת התראות או נתוני משתמש).
    *   `core/forms.py`: (לא סופק תוכן) טופסי Django המשמשים לקבלת קלט מהמשתמשים (לדוגמה, טפסי הרשמה, יצירת קורס). `CourseForm` ו-`UserProfileForm` מוגדרים שם.
    *   `core/middleware.py`: (לא סופק תוכן) שכבת ביניים של Django. `ProfileCompletionMiddleware` אחראי לוודא שהמשתמש השלים את הפרופיל שלו.
    *   `core/models.py`: ליבת המודלים של האפליקציה. מגדיר את כל מבני הנתונים (משתמשים, קורסים, מסמכים, קהילות, סגל אקדמי, סוכן AI, התראות, טרנזקציות מטבעות, צ'אטים) ואת היחסים ביניהם. הוא מייבא את `utils.py` עבור פונקציות עזר כמו `compress_to_webp` ו-`validate_file_size`, ומתחבר ל-`signals.py` באמצעות `@receiver`.
    *   `core/personal_drive.py`: Views המנהלים את הדרייב האישי של המשתמש. מאפשר לראות קבצים שהועלו, היסטוריית הורדות, ומקורות חיצוניים. משתמש במודלים `Document`, `DownloadLog`, `Vote`, `ExternalResource`.
    *   `core/signals.py`: מטפל באיתותים (Signals) של Django. מגיב לאירועים כמו יצירת `Document` חדש (לשליחת התראות) ולכניסת משתמש (למתן בונוס יומי). הוא מייבא מודלים כמו `Document`, `Notification`, `UserCourseSelection` ומשתמש ב-`process_transaction` מ-`utils.py`.
    *   `core/student_agent.py`: (לא סופק תוכן) כנראה הגדרה ספציפית לסוכן AI המיועד לסטודנטים, אולי כחלק מ-`agent_brain.py`.
    *   `core/tasks.py`: (לא סופק תוכן) משימות Celery אסינכרוניות. `process_document_task` מופעל מ-`core/models.py` לעיבוד קבצים ברקע (לדוגמה, חילוץ טקסט).
    *   `core/utils.py`: קובץ כלי עזר כלליים (toolbox). כולל פונקציות לדחיסת תמונות (WebP), אימות גודל וסוג קבצים (Magic Numbers), לוגיקת הרשאות מחיקה חכמה, חילוץ טקסט מ-PDF/DOCX, קבלת IP של משתמש, שליחת התראות, ומנוע לניהול טרנזקציות מטבעות (`process_transaction`). הוא מייבא ספריות כמו `PIL`, `PyPDF2`, `docx`, `filetype`.
    *   `core/__init__.py`: מגדיר את האפליקציה כחבילת Python. במקרה זה, הוא מבצע `import *` מכל קובצי ה-views, מה שמפשט את ה-`urls.py` אך עלול ליצור קונפליקטים בשמות.
    *   `core/management/commands/`: קטגוריית פקודות ניהול מותאמות אישית.
        *   `run_agent.py`: פקודה להרצת סוכן ה-AI.
        *   `seed_academic_data.py`: פקודה להזנת נתונים אקדמיים לדוגמה.
*   **Views (`core/views/`)**:
    *   `core/views/academic.py`: מטפל בניווט אקדמי, חיפוש קורסים, ניהול קורסים ותיקיות, ודירוג סגל. משתמש במודלים כמו `University`, `Major`, `Course`, `Folder`, `Document`, `AcademicStaff` ובפונקציות מ-`utils.py`.
    *   `core/views/accounts.py`: מרכז הבקרה האישי של המשתמש. מנהל פרופיל, הגדרות, אימות סיסמה, התראות וארנק מטבעות. משתמש במודלים `UserProfile`, `Document`, `DownloadLog`, `Notification` וב-`process_transaction` מ-`utils.py`.
    *   `core/views/api.py`: נקודות קצה (Endpoints) ל-AJAX. טעינה דינמית של מסלולי לימוד, הוספת אוניברסיטאות/מסלולים, ומחיקת פריטים באופן גנרי עם בדיקת הרשאות. משתמש במודלים `University`, `Major`, `Document`, `Folder`, `Post`, `Comment` וב-`check_deletion_permission` מ-`utils.py`.
    *   `core/views/documents.py`: ניהול מחזור החיים של המסמכים: העלאה, הורדה, צפייה, סיכום AI, לייקים ודיווחים. כולל `ShareTargetView` לקליטת קבצים מה-OS. משתמש במודלים `Document`, `DownloadLog`, `Major`, `Report`, `Friendship`, `UserCourseSelection`, `Vote`, ובפונקציות מ-`ai_utils.py` ו-`utils.py`.
    *   `core/views/friends_chat.py`: מטפל בפיצ'רים חברתיים: פרופילים ציבוריים, בקשות חברות, רשימת חברים וצ'אט פרטי. משתמש במודלים `Friendship`, `Notification`, `Post`, `Document`, `ChatRoom`, `ChatMessage` וב-`send_notification` מ-`utils.py`.
    *   `core/views/pages.py`: דפים סטטיים (תנאי שימוש, נגישות), עמוד פידבק, דשבורד אנליטיקס למנהלים ועמודי שגיאה (404, 500). משתמש במודלים `Document`, `Course`, `UserProfile`, `Report`, `Feedback`, `Notification`.
    *   `core/views/social.py`: ניהול הפיד הקהילתי. פוסטים, לייקים, תגובות, גילוי קהילות. משתמש במודלים `Community`, `Post`, `MarketplacePost`, `VideoPost`, `Comment`.
*   **טמפלייטים (`core/templates/core/`, `account/`, `socialaccount/`)**:
    *   מכילים את קבצי ה-HTML לעיבוד דפי האתר. מחולקים לפי אזורים לוגיים (כמו `account/` עבור כל ה-views של Allauth). `partials/` מכיל רכיבי HTML שניתנים לשימוש חוזר.
*   **קבצים סטטיים (`core/static/core/`)**:
    *   מכילים את קבצי CSS ו-JavaScript עבור עיצוב ופונקציונליות צד-לקוח. תיקיית `ישן/` מצביעה על קבצים שאינם בשימוש או ישנים.
*   **בדיקות (`core/tests/`)**:
    *   מערכת בדיקות יחידה ואינטגרציה המבטיחות את תקינות הקוד ואת עמידתו בדרישות אבטחה ונגישות.
*   **לוקליזציה (`locale/`)**:
    *   מכיל קבצי תרגום (כמו `.po` או `.mo`) עבור שפות שונות (כרגע אנגלית).

## 📈 2. תמונת מצב וציון בריאות

פרויקט ה-Student Drive מציג פלטפורמה אקדמית עשירה ומורכבת, המשלבת ניהול תוכן לימודי, אינטגרציית AI, פיצ'רים חברתיים (קהילות, צ'אט, חברים), ומערכת גיימיפיקציה (מטבעות). המבנה הכללי מראה על חשיבה רבה סביב הפרדת אחריויות, בעיקר בפיצול קבצי ה-views לתתי-מודולים ייעודיים (academic, documents, social וכו'), וכן שימוש נרחב ב-`select_related` ו-`prefetch_related` המעיד על מודעות לביצועים.

**נקודות חוזקה מרכזיות:**
*   **מודולריות ב-Views:** פיצול ה-Views לקבצים קטנים ומוגדרים היטב משפר מאוד את הקריאות והתחזוקה.
*   **אינטגרציית AI:** הכללת סוכן AI ואפשרות לסיכום מסמכים מראה על חדשנות וערך מוסף לסטודנטים.
*   **אבטחה והרשאות:** קובץ `utils.py` מכיל לוגיקת הרשאות מחיקה חכמה, וכן אימות קבצים באמצעות Magic Numbers, שהיא פרקטיקה אבטחתית מעולה. הגדרות `settings.py` מציגות מודעות גבוהה לאבטחת ססמאות, קוקיז, ושימוש ב-HTTPS.
*   **ביצועים (DB):** שימוש נרחב ב-`select_related` ו-`prefetch_related` ב-QuerySets השונים מצביע על ניסיון למנוע בעיות N+1 ולשפר ביצועי שאילתות.
*   **Celery:** קיים מבנה למשימות רקע (Celery), קריטי לעיבוד קבצים כבדים ולמנוע חסימת שרשורים ראשיים.
*   **ניהול משתמשים מתקדם:** Allauth עם אינטגרציה מלאה ל-Google, כולל התאמה אישית של תהליכי הרשמה והפניות.
*   **גיימיפיקציה ומוטיבציה:** מערכת המטבעות (Coin Transactions) והבונוסים מעודדת השתתפות פעילה בקהילה.
*   **תיעוד פנימי:** קבצי `.md` (כמו `PROJECT_MIRROR.md`) והערות קוד מפורטות מראים על ניסיון לתעד את המערכת.

**נקודות תורפה וחששות:**
*   **קובצי Models ו-Utils מונוליטיים:** `core/models.py` ו-`core/utils.py` גדולים מאוד ומכילים לוגיקה ממגוון רחב של תחומי אחריות. זה עלול להקשות על ניהול, בדיקה והרחבה בעתיד. פיצול שלהם לאפליקציות/מודולים קטנים יותר יהיה מועיל.
*   **ייבוא `*` ב-`core/views/__init__.py`:** ייבוא כללי של כל ה-Views עלול ליצור קונפליקטים בשמות ולפגוע בהבנה מהיכן מגיע כל View. עדיף ייבוא מפורש.
*   **`CELERY_TASK_ALWAYS_EAGER = True` ב-`settings.py`:** למרות שזה טוב לפיתוח ולבדיקות, אם זה נשאר `True` בייצור, משימות רקע יבוצעו באופן סינכרוני, מה שיפגע קשות בביצועים ובסקיילביליות. יש לוודא שההגדרה הזו מושבתת או מוגדרת ל-`False` ב-Production.
*   **לוגיקה עסקית מפוזרת:** למרות קיומן של פונקציות כמו `process_transaction` ו-`send_notification` ב-`utils.py`, הן נקראות ישירות מתוך ה-Views. עדיף לרכז לוגיקה עסקית מורכבת בשכבת Services נפרדת, כדי לשמור על ה-Views רזים וקל יותר לנהל את הטרנזקציות ולבדוק את הקוד.
*   **תיקיית `core/static/ישן/`:** מצביעה על חוסר ניקיון בקבצים סטטיים שאינם בשימוש.
*   **ממשק AI ב-`agent_views.py`:** לוגיקת ה-if/elif המרובה ב-`ask_agent_question` עלולה להיות קשה לתחזוקה ככל שהפיצ'רים של ה-AI יתרחבו.

**ציון בריאות:** 80/100

הפרויקט מציג יסודות טובים ופיצ'רים מרשימים, אך ישנם מספר היבטים ארכיטקטוניים (בעיקר גודל המודולים וחשיבה על שכבת Services) וקונפיגורציה (Celery) שדורשים תשומת לב כדי להבטיח אריכות ימים, סקיילביליות ואמינות ב-Production.

## 🗺️ 3. מפת ארכיטקטורה (Visual Flowchart)

```mermaid
erDiagram
    CustomUser {
        int id PK
        string username
        string role
        string email
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
        int referred_by_id FK "self-referential to CustomUser"
    }

    University {
        int id PK
        string name
        string logo
    }

    Major {
        int id PK
        int university_id FK
        string name
    }

    Course {
        int id PK
        int major_id FK
        string name
        int creator_id FK
    }

    Folder {
        int id PK
        int course_id FK
        int parent_id FK "self-referential"
        string name
        int created_by_id FK
        int staff_member_id FK
    }

    Document {
        int id PK
        int course_id FK
        int folder_id FK
        string title
        string file
        text file_content
        int uploaded_by_id FK
    }

    ExternalResource {
        int id PK
        int user_id FK
        string title
        string link
        string file
    }

    Community {
        int id PK
        string name
        string community_type
        int university_id FK
        int major_id FK
    }

    Post {
        int id PK
        int user_id FK
        text content
        int community_id FK
        int university_id FK
    }

    MarketplacePost ||--o{ Post : "inherits"
    VideoPost ||--o{ Post : "inherits"

    Comment {
        int id PK
        int post_id FK
        int user_id FK
        text text
    }

    AcademicStaff {
        int id PK
        int university_id FK
        string name
        float average_rating
        int created_by_id FK
    }

    Lecturer ||--o{ AcademicStaff : "inherits"
    TeachingAssistant ||--o{ AcademicStaff : "inherits"

    StaffReview {
        int id PK
        int staff_member_id FK
        int user_id FK
        int rating
        string review_text
    }

    CourseSemesterStaff {
        int id PK
        int course_id FK
        int staff_member_id FK
        int academic_year
        string semester
    }

    Friendship {
        int id PK
        int user_from_id FK
        int user_to_id FK
        string status
    }

    ChatRoom {
        int id PK
        string name
    }

    ChatMessage {
        int id PK
        int room_id FK
        int sender_id FK
        text content
        int attached_file_id FK
    }

    Notification {
        int id PK
        int user_id FK
        int sender_id FK
        string notification_type
        string title
        text message
        string link
        int content_type_id FK
        int object_id
    }

    AgentKnowledge {
        int id PK
        int owner_id FK
        string file
        string course_name
        text extracted_text
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

    CoinTransaction {
        int id PK
        int user_id FK
        int actor_id FK
        int amount
        string transaction_type
    }

    UserCourseSelection {
        int id PK
        int user_id FK
        int course_id FK
        boolean is_starred
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
        text message
    }

    DocumentComment {
        int id PK
        int document_id FK
        int user_id FK
        text text
    }


    CustomUser ||--o{ UserProfile : "One-to-One"
    CustomUser ||--o{ UserCourseSelection : "has many"
    CustomUser ||--o{ Friendship : "sends/receives many"
    CustomUser ||--o{ ChatRoom : "participates in many"
    CustomUser ||--o{ ChatMessage : "sends many"
    CustomUser ||--o{ Notification : "receives many"
    CustomUser ||--o{ AgentKnowledge : "owns many"
    CustomUser ||--o{ DownloadLog : "creates many"
    CustomUser ||--o{ Vote : "casts many"
    CustomUser ||--o{ CoinTransaction : "has many"
    CustomUser ||--o{ Post : "creates many"
    CustomUser ||--o{ Comment : "creates many"
    CustomUser ||--o{ DocumentComment : "creates many"
    CustomUser ||--o{ ExternalResource : "owns many"
    CustomUser ||--o{ Report : "creates many"
    CustomUser ||--o{ Feedback : "creates many"
    CustomUser ||--o{ Community : "joins many"

    UserProfile }o--|| University : "is in one"
    UserProfile }o--|| Major : "studies one"
    UserProfile }o--|| Course : "favorites many"

    Major }o--|| University : "belongs to one"
    Course }o--|| Major : "belongs to one"
    Course }o--|| CustomUser : "created by"
    Course }o--|| Folder : "has many"
    Course }o--|| Document : "contains many"
    Course }o--|| CourseSemesterStaff : "has many"
    Course }o--|| UserCourseSelection : "selected by many"

    Folder }o--|| Course : "belongs to one"
    Folder }o--o| Folder : "can have parent"
    Folder }o--|| AcademicStaff : "associated with"
    Folder }o--|| CustomUser : "created by"
    Folder }o--|| Document : "contains many"

    Document }o--|| Course : "belongs to one"
    Document }o--o| Folder : "is in one"
    Document }o--|| CustomUser : "uploaded by"
    Document }o--|| AcademicStaff : "associated with"
    Document }o--|| Vote : "has many"
    Document }o--|| DownloadLog : "has many"
    Document }o--|| Report : "has many"
    Document }o--|| DocumentComment : "has many"

    Post }o--|| CustomUser : "created by"
    Post }o--|| Community : "belongs to one"
    Post }o--|| University : "associated with"
    Post }o--|| Comment : "has many"
    Post }o--|| CustomUser : "liked by many"

    Comment }o--|| Post : "belongs to one"
    Comment }o--|| CustomUser : "created by"

    AcademicStaff }o--|| University : "belongs to one"
    AcademicStaff }o--|| StaffReview : "has many"
    AcademicStaff }o--|| CourseSemesterStaff : "participates in many"
    AcademicStaff }o--o| CustomUser : "created by"

    StaffReview }o--|| AcademicStaff : "reviews one"
    StaffReview }o--|| CustomUser : "created by"

    CourseSemesterStaff }o--|| Course : "relates to one"
    CourseSemesterStaff }o--|| AcademicStaff : "has one"

    Friendship }o--|| CustomUser : "user_from"
    Friendship }o--|| CustomUser : "user_to"

    ChatRoom }o--* CustomUser : "has many participants"
    ChatRoom }o--|| ChatMessage : "has many messages"

    ChatMessage }o--|| ChatRoom : "belongs to one"
    ChatMessage }o--|| CustomUser : "sent by"
    ChatMessage }o--o| Document : "attaches one"

    Notification }o--|| CustomUser : "for user"
    Notification }o--o| CustomUser : "sent by"
    Notification }o--o| ContentType : "targets type"

    AgentKnowledge }o--|| CustomUser : "owned by"

    DownloadLog }o--|| Document : "logs download of"

    Vote }o--|| Document : "votes on"

    CoinTransaction }o--|| CustomUser : "for user"
    CoinTransaction }o--o| CustomUser : "actor"

    UserCourseSelection }o--|| Course : "selects"

    Report }o--|| Document : "reports"

    Feedback }o--o| CustomUser : "from user"
    DocumentComment }o--|| Document : "comments on"
    DocumentComment }o--|| CustomUser : "created by"
```

## 💡 4. ביקורת קוד אדריכלית (Code Review)

להלן 3-5 המלצות אדריכליות ברמה גבוהה:

1.  **פיצול אפליקציית ה-`core` לאפליקציות Django קטנות וממוקדות (Microservices-like structure):**
    *   **תיאור:** אפליקציית ה-`core` גדולה מאוד ומכילה מגוון רחב של תחומי אחריות (משתמשים, אקדמיה, מסמכים, קהילות, צ'אט, AI, כלכלה). קובצי המודלים (`core/models.py`) וכלי העזר (`core/utils.py`) מונוליטיים ומכילים מאות שורות קוד המתארות לוגיקה שונה לחלוטין.
    *   **המלצה:** פצל את אפליקציית ה-`core` לאפליקציות Django קטנות יותר, לדוגמה: `users_and_auth`, `academic`, `documents_and_storage`, `social_feed`, `chat_and_friends`, `ai_agent`, `economy`. כל אפליקציה תכלול את המודלים, ה-views, הטמפלייטים, הטפסים וכלי העזר הרלוונטיים לה. זה ישפר באופן דרמטי את יכולת התחזוקה, הסקיילביליות ויאפשר עבודה בצוותים קטנים יותר על רכיבים שונים.
    *   **יתרון אדריכלי:** הפרדת אחריויות (Separation of Concerns), שיפור ה-Module Cohesion, הפחתת ה-Coupling, שיפור ביצועי טעינה (imports), ובדיקוּת (testability) קלה יותר.

2.  **הטמעת שכבת Service ייעודית ללוגיקה עסקית מורכבת:**
    *   **תיאור:** לוגיקה עסקית משמעותית, כמו ניהול טרנזקציות מטבעות (`process_transaction`), שליחת התראות (`send_notification`), או אפילו תהליך עיבוד מסמכים (הפעלה של Celery task ושמירת תוצאות), מפוזרת כיום בין ה-`views.py`, `models.py` ו-`signals.py`. זה מוביל לכפילויות קוד ולוגיקה עסקית שאינה ניתנת לשימוש חוזר בקלות.
    *   **המלצה:** צור שכבת `services.py` או `managers.py` בתוך כל אפליקציה מפוצלת (ראה המלצה 1). פונקציות כמו `process_transaction` צריכות להיות חלק מ-Service שנקרא מה-View/Signal. לדוגמה, `economy.services.process_user_transaction(user, amount, type, description)`. ה-Views צריכים רק לקרוא לשירותים אלה ולטפל בתגובה.
    *   **יתרון אדריכלי:** עקרון ה-DRY (Don't Repeat Yourself), עקרון ה-Single Responsibility Principle (SRP) עבור ה-Views, שיפור הבדיקוּת (קל יותר לבדוק יחידות לוגיות שלמות), ושיפור בהפשטה (Abstraction) של הלוגיקה העסקית.

3.  **הבטחת קונפיגורציית Celery נכונה ומאובטחת עבור Production:**
    *   **תיאור:** קובץ `settings.py` מגדיר `CELERY_TASK_ALWAYS_EAGER = True`. בעוד שזה אידיאלי לסביבת פיתוח ובדיקות (מבצע משימות באופן סינכרוני ומונע צורך ב-Broker פעיל), זו תהיה תקלה קריטית בסביבת Production, שבה המשימות צריכות לרוץ ברקע באופן אסינכרוני.
    *   **המלצה:** וודא כי `CELERY_TASK_ALWAYS_EAGER` מוגדר במפורש ל-`False` כאשר `DEBUG = False`. בנוסף, יש להבטיח כי ה-`CELERY_BROKER_URL` וה-`CELERY_RESULT_BACKEND` מצביעים לשרת Redis מאובטח וזמין ב-Production. יש לתעד היטב את תהליך הפריסה של Celery worker ו-beat.
    *   **יתרון אדריכלי:** הבטחת סקיילביליות ואמינות המערכת ב-Production על ידי ניצול נכון של עיבוד אסינכרוני, מניעת חסימות ב-Web server ושיפור חווית המשתמש.

4.  **שיפור ניהול קבצים סטטיים ומדיה:**
    *   **תיאור:** קיימת תיקייה `core/static/ישן/` המעידה על קבצים סטטיים שאינם בשימוש ואינם מנוקים. כמו כן, קיים סיכון ל-Path Traversal או XSS אם קבצים סטטיים/מדיה בעייתיים נשארים נגישים.
    *   **המלצה:** נקה את תיקיית ה-`ישן/` והטמע תהליך ניקוי קבוע (למשל, כחלק מתהליך CI/CD או פקודת ניהול). עבור קבצי מדיה, וודא ש-`AWS_QUERYSTRING_AUTH = False` נבדק היטב בהקשר של פרטיות קבצים המועלים על ידי משתמשים (לדוגמה, אם יש קבצים פרטיים שאמורים להיות נגישים רק לבעליהם).
    *   **יתרון אדריכלי:** שיפור אבטחה, יעילות אחסון, וניקיון קוד.

## ✅ 5. צ'ק-ליסט משימות (Action Items)

- [ ] **פצל את אפליקציית ה-`core` לאפליקציות Django קטנות ומוגדרות יותר:**
    *   צור אפליקציות חדשות כמו `users`, `academic`, `documents`, `social`, `chat`, `ai_agent`, `economy`.
    *   העבר את המודלים, ה-views, הטפסים, ה-URLs והכלי העזר הרלוונטיים לכל אפליקציה חדשה.
    *   עדכן את הייבואים והיחסים בין המודלים (לדוגמה, `users.CustomUser` במקום `core.CustomUser`).
- [ ] **הקם שכבת Service ייעודית ללוגיקה עסקית:**
    *   עבור על כל קריאות לפונקציות כמו `process_transaction` ו-`send_notification` מתוך ה-Views וה-Signals.
    *   העבר את לוגיקת הטרנזקציות וההתראות לשירותים מוגדרים (לדוגמה, `economy.services.handle_referral_bonus(...)`).
    *   ודא שה-Views רק קוראים לשירותים אלה ומטפלים בתגובות (שגיאות/הצלחה).
- [ ] **הגדר את Celery לקראת Production:**
    *   ודא שההגדרה `CELERY_TASK_ALWAYS_EAGER` ב-`settings.py` תלויה במצב `DEBUG` (כלומר `False` ב-Production).
    *   בדוק וודא ש-`CELERY_BROKER_URL` ו-`CELERY_RESULT_BACKEND` מצביעים לשרת Redis תקין ומאובטח בסביבת Production.
    *   תעד והכן את תהליכי הפריסה והניטור של Celery workers ו-Celery beat.

---
*נבנה באהבה על ידי סוכן ה-AI שלך 🤖 | מופעל באמצעות Gemini 2.5 Flash*

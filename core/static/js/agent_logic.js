document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('agent-toggle-btn');
    const chatWindow = document.getElementById('agent-chat-window');
    const closeBtn = document.getElementById('agent-close-btn');
    const fileInput = document.getElementById('agent-file-input');
    const sendBtn = document.getElementById('agent-send-btn');
    const userInput = document.getElementById('agent-user-input');
    const messagesContainer = document.getElementById('agent-messages');
    const agentTitle = document.querySelector('.agent-header span');
    const quizBtn = document.getElementById('quiz-mode-btn');

    // חילוץ שם המשתמש מהכותרת
    const userName = agentTitle ? agentTitle.innerText.replace('הסוכן של', '').trim() : "עמית";

    function showWelcomeMessage() {
        if (messagesContainer.children.length === 0) {
            const welcomeText = `היי ${userName}! אני הסוכן האישי שלך. אני יכול לסכם קבצים, לענות על שאלות מהקורסים או לבחון אותך במצב Quiz Mode. מה נלמד היום?`;
            addMessage(welcomeText, 'agent');
        }
    }

    // פתיחה וסגירה של חלונית הצ'אט
    toggleBtn.onclick = () => {
        chatWindow.classList.toggle('agent-hidden');
        showWelcomeMessage();
    };

    closeBtn.onclick = () => chatWindow.classList.add('agent-hidden');

    // פונקציית עזר לקבלת CSRF Token מהדף
    function getCSRFToken() {
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenInput ? tokenInput.value : '';
    }

    // הוספת הודעה למסך
    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = type === 'user' ? 'user-msg' : 'agent-msg';
        div.style.whiteSpace = 'pre-wrap';
        div.innerText = text;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // --- פונקציה ליצירת כפתורי בחירת קורס בתוך הצ'אט ---
    function addCourseSelectionButtons(text, courses) {
        const mainDiv = document.createElement('div');
        mainDiv.className = 'agent-msg';

        const promptText = document.createElement('div');
        promptText.innerText = text;
        promptText.style.marginBottom = '10px';
        mainDiv.appendChild(promptText);

        const btnContainer = document.createElement('div');
        btnContainer.className = 'd-flex flex-wrap gap-2';

        courses.forEach(course => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-primary btn-sm quiz-choice-btn';
            btn.innerText = course;
            btn.style.borderRadius = '15px';
            btn.style.fontSize = '12px';
            btn.style.margin = '2px';
            btn.style.padding = '5px 12px';

            btn.onclick = () => {
                addMessage(course, 'user');
                sendMessage(`בוחן בקורס: ${course}`);
                btnContainer.querySelectorAll('button').forEach(b => b.disabled = true);
            };
            btnContainer.appendChild(btn);
        });

        mainDiv.appendChild(btnContainer);
        messagesContainer.appendChild(mainDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // --- [חדש] פונקציה להצגת כפתורי ה"כן/לא" להצעה לידע כללי ---
    function addGeneralKnowledgeButtons(text, course) {
        const mainDiv = document.createElement('div');
        mainDiv.className = 'agent-msg';

        const promptText = document.createElement('div');
        promptText.innerText = text;
        promptText.style.marginBottom = '10px';
        mainDiv.appendChild(promptText);

        const btnContainer = document.createElement('div');
        btnContainer.className = 'd-flex gap-2';

        const yesBtn = document.createElement('button');
        yesBtn.className = 'btn btn-sm btn-success';
        yesBtn.innerText = 'כן, בטח';
        yesBtn.style.borderRadius = '15px';

        const noBtn = document.createElement('button');
        noBtn.className = 'btn btn-sm btn-secondary';
        noBtn.innerText = 'לא, תודה';
        noBtn.style.borderRadius = '15px';

        yesBtn.onclick = () => {
            addMessage("כן, בטח", 'user');
            sendMessage(`ייצר שאלות כלליות ב: ${course}`);
            btnContainer.querySelectorAll('button').forEach(b => b.disabled = true);
        };

        noBtn.onclick = () => {
            addMessage("לא, תודה", 'user');
            addMessage("אין בעיה! אני כאן אם תרצה לשאול משהו אחר או להעלות קבצים.", 'agent');
            btnContainer.querySelectorAll('button').forEach(b => b.disabled = true);
        };

        btnContainer.appendChild(yesBtn);
        btnContainer.appendChild(noBtn);
        mainDiv.appendChild(btnContainer);
        messagesContainer.appendChild(mainDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // פונקציה מרכזית לשליחת הודעה/שאלה
    async function sendMessage(customText = null) {
        const question = customText || userInput.value.trim();
        if (!question) return;

        if (!customText) {
            addMessage(question, 'user');
            userInput.value = '';
        }

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'agent-msg loading';
        loadingDiv.innerText = 'מעבד נתונים...';
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            // 1. נסיון חכם לחלץ את שם הקורס מהעמוד הנוכחי
            // מחפש את כותרת העמוד (h1). אם זה לא קורס, זה יעביר "כללי"
            let currentCourseName = 'כללי';
            const pageTitle = document.querySelector('h1');
            if (pageTitle) {
                currentCourseName = pageTitle.innerText.trim();
            }

            // 2. השליחה לשרת (מוסיפים את current_course לגוף הבקשה)
            const response = await fetch('/agent/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    question: question,
                    current_course: currentCourseName // <--- הקונטקסט!
                })
            });
            const data = await response.json();
            messagesContainer.removeChild(loadingDiv);

            // בדיקת סוג התגובה מהשרת
            if (data.type === 'course_selection') {
                addCourseSelectionButtons(data.answer, data.courses);
            } else if (data.type === 'general_knowledge_offer') {
                addGeneralKnowledgeButtons(data.answer, data.course);
            } else {
                addMessage(data.answer, 'agent');
            }
        } catch (error) {
            if (loadingDiv.parentNode) messagesContainer.removeChild(loadingDiv);
            addMessage("שגיאה בתקשורת עם השרת.", 'agent');
        }
    }

    // לוגיקת Quiz Mode
    if (quizBtn) {
        quizBtn.onclick = async function() {
            await sendMessage("GET_COURSES_FOR_QUIZ");
        };
    }

    sendBtn.onclick = () => sendMessage();
    userInput.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };

    // העלאת קובץ
    fileInput.onchange = async function() {
        const file = fileInput.files[0];
        if (!file) return;

        addMessage(`מעלה קובץ: ${file.name}...`, 'user');

        const formData = new FormData();
        formData.append('file', file);

        const pageTitle = document.querySelector('h1')?.innerText || "כללי";
        formData.append('course_name', pageTitle);

        try {
            const response = await fetch('/agent/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });
            const data = await response.json();
            if (data.status === 'success') {
                addMessage("הקובץ נלמד בהצלחה! הנה סיכום קצר:", 'agent');
                addMessage(data.summary, 'agent');
            } else {
                addMessage("חלה שגיאה בעיבוד הקובץ.", 'agent');
            }
        } catch (error) {
            addMessage("שגיאה טכנית בהעלאה.", 'agent');
        }
    };
});
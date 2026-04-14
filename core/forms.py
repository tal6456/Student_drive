"""
מערכת טפסים ואימות נתונים (Forms System)
=======================================

מה המטרה של הקובץ הזה?
----------------------
קובץ זה מנהל את כל הקלט מהמשתמשים באתר. הוא אחראי לייצר טפסים מאובטחים, 
מעוצבים וידידותיים למשתמש, תוך הקפדה שהמידע שנכנס למערכת תקין.

הקובץ מטפל ב-4 תחומים מרכזיים:
1. אוטומיזציה של עיצוב (BaseStyledModelForm): מנוע חכם שמזריק אוטומטית 
   עיצוב Bootstrap ומצב לילה לכל שדה בטופס, מה שחוסך עבודה ידנית רבה.
2. ניהול תוכן (Document & Course): טפסים להעלאת קבצים ויצירת קורסים. 
   הם כוללים לוגיקה למניעת כפילויות (למשל: התראה אם קורס כבר קיים) 
   ובדיקת זכויות יוצרים.
3. ניהול רישום (Signup): אינטגרציה עם מערכת ההתחברות כדי להכריח משתמשים 
   לאשר את תנאי השימוש ומדיניות הפרטיות כבר בשלב ההרשמה.
4. השלמת פרופיל: טופס מורכב המאפשר לסטודנטים לעדכן פרטים אישיים, 
   מוסד לימודים ומסלול, תוך סנכרון המידע בין מודל המשתמש למודל הפרופיל.

השימוש בטפסים אלו מבטיח הגנה מפני הזרקות קוד (XSS) ושומר על אחידות 
ויזואלית בכל רחבי האתר.
-----------------------------------------------
עלינו לדאוג שבקובץ הזה מאוחסנים נושא הטפסים מול המשתמש באתר!!
"""

import re

from django import forms
from django.contrib.auth import get_user_model
from .models import Document, Course, UserProfile, Folder
from django.urls import reverse
from django.utils.safestring import mark_safe

# משיכת מודל המשתמש החדש שלנו (CustomUser) בצורה בטוחה
User = get_user_model()


# ==========================================
# 1. טופס האב: מכונת העיצוב האוטומטית
# ==========================================
class BaseStyledModelForm(forms.ModelForm):
    """
    טופס בסיס שכל הטפסים באתר יירשו ממנו.
    הוא עובר אוטומטית על כל השדות ומזריק להם עיצוב של Bootstrap ומצב לילה,
    כך שלא צריך לכתוב widget class לכל שדה בנפרד!
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (
            forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Select, forms.Textarea, forms.FileInput)):
                base_class = 'form-select form-select-lg' if isinstance(field.widget,
                                                                        forms.Select) else 'form-control form-control-lg'
                field.widget.attrs.update({
                    'class': f'{base_class} border-0 shadow-sm mb-3',
                    'style': 'background-color: var(--gd-bg) !important; color: var(--gd-text) !important;'
                })


# --- טופס להעלאת קבצים (מותאם למבנה התיקיות החדש וללא אנונימיות) ---
class DocumentUploadForm(BaseStyledModelForm):
    new_folder_name = forms.CharField(
        required=False,
        label="או צור תיקייה חדשה בשם:",
        widget=forms.TextInput(attrs={'placeholder': 'לדוגמה: סיכומי הרצאות, מבחנים...'})
    )

    copyright_confirm = forms.BooleanField(
        required=True,
        label="אני מצהיר/ה שהקובץ שייך לי או שיש לי רשות לשתפו, ושהוא אינו מפר זכויות יוצרים של המרצה או המוסד.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input mb-3'})
    )

    class Meta:
        model = Document
        fields = ['title', 'file', 'folder', 'staff_member']

        labels = {
            'title': 'שם הקובץ',
            'folder': 'בחר תיקייה קיימת',
            'staff_member': 'מרצה / מתרגל (לא חובה - עוזר לדירוגים!)',
        }


# --- טופס ליצירת קורס חדש (מנוע חכם נגד כפילויות) ---
class CourseForm(BaseStyledModelForm):
    class Meta:
        model = Course
        fields = ['major', 'name', 'course_number', 'year', 'semester', 'track', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'לדוגמה: מבוא למדעי המחשב'}),
            'course_number': forms.TextInput(attrs={'placeholder': 'מספר קורס (לא חובה)'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'סילבוס או תיאור קצר (לא חובה)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['major'].required = True
        self.fields['year'].required = True

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name_clean = name.strip()
            exact_match = Course.objects.filter(name=name_clean).first()
            if exact_match:
                raise forms.ValidationError(f"הקורס '{exact_match.name}' כבר קיים במערכת! חזור לדף הבית וחפש אותו.")

            similar_course = Course.objects.filter(name__icontains=name_clean).first()
            if similar_course:
                raise forms.ValidationError(
                    f"רגע! כבר קיים במערכת קורס בשם '{similar_course.name}'. האם התכוונת אליו? "
                    f"אם זה קורס שונה, אנא תן לו שם מדויק יותר."
                )
        return name


# --- טופס שמתממשק ישירות עם django-allauth כדי להוסיף תנאי שימוש ---
class CustomSignupForm(forms.Form):
    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={'required': 'חובה לאשר את התנאים כדי להמשיך למערכת.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2', 'style': 'cursor: pointer;'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # הזרקת הלינקים מתבצעת רק לאחר שהטופס נטען
        self.fields['terms_accepted'].label = mark_safe(
            f'אני קראתי ומאשר/ת את <a href="{reverse("terms")}" class="text-primary text-decoration-none fw-bold" target="_blank">תנאי השימוש</a> ואת <a href="{reverse("privacy")}" class="text-primary text-decoration-none fw-bold" target="_blank">מדיניות הפרטיות</a>'
        )

    def signup(self, request, user):
        pass


# --- טופס להשלמת פרטי פרופיל (מותאם לכולם - סטודנטים וקהל רחב) ---
class UserProfileForm(BaseStyledModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="שם פרטי")
    last_name = forms.CharField(max_length=30, required=True, label="שם משפחה")

    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={'required': 'חובה לאשר את התנאים כדי להמשיך למערכת.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2', 'style': 'cursor: pointer;'})
    )

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'university', 'major', 'year']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # הזרקת הלינקים מתבצעת רק לאחר שהטופס נטען
        self.fields['terms_accepted'].label = mark_safe(
            f'אני קראתי ומאשר/ת את <a href="{reverse("terms")}" class="text-primary text-decoration-none fw-bold" target="_blank">תנאי השימוש</a> ואת <a href="{reverse("privacy")}" class="text-primary text-decoration-none fw-bold" target="_blank">מדיניות הפרטיות</a>'
        )

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

        self.fields['university'].required = False
        self.fields['university'].empty_label = "--- לא סטודנט / ללא שיוך ---"
        self.fields['major'].required = False
        self.fields['major'].empty_label = "--- ללא מסלול ---"
        self.fields['year'].required = False
        self.fields['year'].empty_label = "--- לא רלוונטי ---"
        self.fields['phone_number'].required = False
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'לדוגמה: 0501234567',
            'type': 'tel',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        })

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            return phone_number

        # Normalize number by stripping spaces, dashes and parentheses.
        normalized = re.sub(r'[\s\-()]+', '', phone_number)

        valid_pattern = re.compile(r'^(?:\+9725\d{8}|05\d{8}|\+972[23489]\d{7}|0[23489]\d{7})$')
        if not valid_pattern.match(normalized):
            raise forms.ValidationError(
                'המספר שהוזן לא תקין. אנא הקלד מספר ישראלי תקין כמו 0501234567 או +972501234567.'
            )

        return normalized

    def clean(self):
        cleaned_data = super().clean()
        uni = cleaned_data.get('university')
        major = cleaned_data.get('major')

        if major and not uni:
            self.add_error('university', "חובה לבחור מוסד לימודים אם בחרת מסלול.")

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile.save()
        return profile
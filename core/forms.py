from django import forms
from django.contrib.auth.models import User
from .models import Document, Course, UserProfile, Folder


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


# --- טופס להעלאת קבצים (מותאם למבנה התיקיות החדש) ---
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
        # שינינו כאן מ-lecturer ל-staff_member
        fields = ['title', 'file', 'folder', 'staff_member', 'is_anonymous']
        labels = {
            'title': 'שם הקובץ',
            'folder': 'בחר תיקייה קיימת',
            # שינינו גם כאן את המפתח כדי שהתווית תוצמד לשדה הנכון
            'staff_member': 'מרצה / מתרגל (לא חובה - עוזר לדירוגים!)',
            'is_anonymous': 'העלאה אנונימית (השם שלך לא יופיע על הקובץ)',
        }
        widgets = {
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        label="אני מאשר/ת את תנאי השימוש ומדיניות הפרטיות של האתר",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2', 'style': 'cursor: pointer;'})
    )

    def signup(self, request, user):
        pass


# --- טופס להשלמת פרטי פרופיל סטודנט (הפרופיל המדורג) ---
class UserProfileForm(BaseStyledModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="שם פרטי (אפשר גם כינוי)")
    last_name = forms.CharField(max_length=30, required=True, label="שם משפחה")

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'university', 'major', 'year']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

        self.fields['university'].required = True
        self.fields['university'].empty_label = "--- בחרו מוסד לימודים ---"
        self.fields['major'].required = True
        self.fields['major'].empty_label = "--- בחרו פקולטה / מסלול ---"
        self.fields['year'].required = True
        self.fields['year'].empty_label = "--- בחרו שנת לימוד ---"

        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'לדוגמה: 0501234567'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile.save()
        return profile
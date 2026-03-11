from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Document

# טופס להעלאת קבצים
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'category', 'is_anonymous'] # הוספנו את is_anonymous

# טופס להרשמת משתמש חדש עם אישור תנאים
class UserRegisterForm(UserCreationForm):
    # הוספת אימייל כשדה חובה
    email = forms.EmailField(required=True, label="כתובת אימייל")

    terms_accepted = forms.BooleanField(
        required=True,
        label="אני מאשר את תנאי השימוש ומדיניות הפרטיות"
    )

    class Meta:
        model = User
        fields = ['username', 'email']  # וודא שאימייל מופיע כאן
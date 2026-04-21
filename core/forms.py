"""
Forms and validation system
===========================

What is this file for?
----------------------
This file manages all user input across the site. It is responsible for
building secure, well-styled, and user-friendly forms while making sure
incoming data is valid.

It covers four main areas:
1. Styling automation (`BaseStyledModelForm`): a smart base form that injects
   Bootstrap and dark-mode styling into each field automatically.
2. Content management (`Document` and `Course`): forms for uploading files and
   creating courses, including duplicate-prevention logic and copyright checks.
3. Signup flow: integrates with the authentication system to require users to
   accept the terms and privacy policy during registration.
4. Profile completion: a richer form that lets students update personal and
   academic details while syncing data between the user and profile models.

Using these forms helps protect the site from invalid input and keeps the UI
consistent throughout the project.
"""

import re

from django import forms
from django.contrib.auth import get_user_model
from .models import Document, Course, UserProfile, Folder
from django.urls import reverse
from django.utils.safestring import mark_safe

# Safely load the custom user model
User = get_user_model()


# ==========================================
# 1. Base form: the automatic styling engine
# ==========================================
class BaseStyledModelForm(forms.ModelForm):
    """
    Base form class inherited by the site's forms.
    It automatically walks through the fields and injects Bootstrap and
    dark-mode styling so each widget does not need to be styled manually.
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


# --- File upload form (adapted to the new folder structure and non-anonymous uploads) ---
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


# --- New course form (smart duplicate prevention) ---
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
            queryset = Course.objects.filter(name=name_clean)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            exact_match = queryset.first()
            if exact_match:
                raise forms.ValidationError(f"הקורס '{exact_match.name}' כבר קיים במערכת! חזור לדף הבית וחפש אותו.")

            similar_qs = Course.objects.filter(name__icontains=name_clean)
            if self.instance and self.instance.pk:
                similar_qs = similar_qs.exclude(pk=self.instance.pk)
            similar_course = similar_qs.first()
            if similar_course:
                raise forms.ValidationError(
                    f"רגע! כבר קיים במערכת קורס בשם '{similar_course.name}'. האם התכוונת אליו? "
                    f"אם זה קורס שונה, אנא תן לו שם מדויק יותר."
                )
        return name


# --- Form that integrates directly with `django-allauth` to add terms acceptance ---
class CustomSignupForm(forms.Form):
    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={'required': 'חובה לאשר את התנאים כדי להמשיך למערכת.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input ms-2', 'style': 'cursor: pointer;'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject the links only after the form is initialized
        self.fields['terms_accepted'].label = mark_safe(
            f'אני קראתי ומאשר/ת את <a href="{reverse("terms")}" class="text-primary text-decoration-none fw-bold" target="_blank">תנאי השימוש</a> ואת <a href="{reverse("privacy")}" class="text-primary text-decoration-none fw-bold" target="_blank">מדיניות הפרטיות</a>'
        )

    def signup(self, request, user):
        pass


# --- Profile completion form (works for students and general users alike) ---
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
        labels = {
            'phone_number': 'מספר טלפון נייד (חובה)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Inject the links only after the form is initialized
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
        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'לדוגמה: 0501234567',
            'type': 'tel',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        })

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        # 1. בדיקה שהשדה לא ריק (ליתר ביטחון)
        if not phone_number:
            raise forms.ValidationError("חובה להזין מספר טלפון כדי להמשיך.")

        # 2. ניקוי תווים מיותרים (רווחים, מקפים)
        normalized = re.sub(r'[\s\-()]+', '', phone_number)

        # 3. רגקס קשוח לנייד ישראלי בלבד (05X-XXXXXXX או עם קידומת +972)
        # מאפשר: 0501234567 או 972501234567+
        valid_pattern = re.compile(r'^(?:05\d{8}|\+9725\d{8})$')

        if not valid_pattern.match(normalized):
            raise forms.ValidationError(
                'נא להזין מספר טלפון נייד ישראלי תקין (לדוגמה: 0501234567).'
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

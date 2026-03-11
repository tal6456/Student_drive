from django.contrib import admin
from .models import University, Major, Course, Document

admin.site.register(University)
admin.site.register(Major)
admin.site.register(Course)
admin.site.register(Document)
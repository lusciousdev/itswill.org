from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Pet)
admin.site.register(CopyPasteGroup, CopyPasteGroupAdmin)
admin.site.register(Ascii, AsciiAdmin)
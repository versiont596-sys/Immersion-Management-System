from django.contrib import admin
from .models import DailyJournal

@admin.register(DailyJournal)
class DailyJournalAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status')
    list_filter = ('status',)

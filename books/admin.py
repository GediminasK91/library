from django.contrib import admin
from .models import Book, BookLoan

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'qr_code')

@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'user_email', 'taken_at', 'returned_at', 'is_returned')
    list_filter = ('returned_at',)

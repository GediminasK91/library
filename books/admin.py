# books/admin.py
from django.contrib import admin
from .models import Book, BookLoan

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "owner")
    list_filter = ("owner",)
    search_fields = ("title", "author", "owner__username", "owner__email", "owner__first_name", "owner__last_name")
    raw_id_fields = ("owner",)

@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ("book", "user_email", "taken_at", "returned_at", "is_returned")
    list_filter = ("returned_at",)
    search_fields = ("user_email", "book__title")

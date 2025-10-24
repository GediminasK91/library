# books/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils import timezone
from io import BytesIO
import qrcode

from django.contrib.auth import get_user_model
User = get_user_model()


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    # NEW: who this book belongs to (employee or service account)
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_books",
        help_text="Who owns this book (e.g., the employee who lent it to the company).",
    )
    qr_code = models.ImageField(upload_to="qr_codes", blank=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)  # Save once to get ID
        if creating and not self.qr_code:
            base_url = getattr(settings, "SITE_BASE_URL", "http://localhost:8000")
            qr_url = f"{base_url}{reverse('take_book_page', args=[self.id])}"
            qr = qrcode.make(qr_url)
            buffer = BytesIO()
            qr.save(buffer)
            self.qr_code.save(
                f"qr_code_{self.id}.png",
                ContentFile(buffer.getvalue()),
                save=False,
            )
            super().save(update_fields=["qr_code"])

    def __str__(self):
        return self.title


class BookLoan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user_email = models.EmailField()
    taken_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["book"],
                condition=models.Q(returned_at__isnull=True),
                name="unique_active_loan_per_book",
            )
        ]
        indexes = [
            models.Index(fields=["book"]),
            models.Index(fields=["returned_at"]),
        ]

    @property
    def is_returned(self):
        return self.returned_at is not None

    def __str__(self):
        return f"{self.book.title} loaned to {self.user_email}"

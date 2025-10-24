from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.files.base import ContentFile
from io import BytesIO
import qrcode


class Book(models.Model):
    """
    Represents a book in the company library.
    Each book can optionally have an 'owner' (a person or department name)
    and a generated QR code that links to its take page.
    """

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)

    # ✅ Owner is now plain text, not a ForeignKey
    owner = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of the person or department who owns this book",
    )

    qr_code = models.ImageField(upload_to="qr_codes", blank=True)

    def save(self, *args, **kwargs):
        """Generate QR code only when a new Book is created."""
        creating = self.pk is None
        super().save(*args, **kwargs)  # Save once to get an ID

        if creating and not self.qr_code:
            base_url = getattr(settings, "SITE_BASE_URL", "http://localhost:8000")
            qr_url = f"{base_url}{reverse('take_book_page', args=[self.id])}"
            qr = qrcode.make(qr_url)
            buf = BytesIO()
            qr.save(buf)
            self.qr_code.save(
                f"qr_code_{self.id}.png",
                ContentFile(buf.getvalue()),
                save=False,
            )
            super().save(update_fields=["qr_code"])

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookLoan(models.Model):
    """
    Represents an active or completed loan of a book.
    A book can only have one active (not returned) loan at a time.
    """

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
            ),
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

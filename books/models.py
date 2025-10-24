from django.db import models
from django.conf import settings
from django.urls import reverse
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

    # ✅ Owner is plain text
    owner = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of the person or department who owns this book",
    )

    # ✅ QR code stored as binary data inside the DB instead of file
    qr_image = models.BinaryField(blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        """Generate QR code only when a new Book is created."""
        creating = self.pk is None
        super().save(*args, **kwargs)  # Save once to get ID

        if creating and not self.qr_image:
            base_url = getattr(settings, "SITE_BASE_URL", "http://localhost:8000")
            qr_url = f"{base_url}{reverse('take_book_page', args=[self.id])}"
            qr = qrcode.make(qr_url)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            self.qr_image = buf.getvalue()
            super().save(update_fields=["qr_image"])

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

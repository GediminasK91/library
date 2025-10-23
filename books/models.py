from django.db import models
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)  # Save once to get an ID
        # Only generate QR code if object was just created or QR code is missing
        if creating and not self.qr_code:
            qr = qrcode.make(f'http://localhost:8000/books/take/{self.id}/')
            canvas = BytesIO()
            qr.save(canvas)
            self.qr_code.save(f'qr_code_{self.id}.png', ContentFile(canvas.getvalue()), save=False)
            super().save(update_fields=['qr_code'])  # Only update the qr_code field

    def __str__(self):
        return self.title

class BookLoan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user_email = models.EmailField()
    taken_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_returned(self):
        return self.returned_at is not None

    def __str__(self):
        return f"{self.book.title} loaned to {self.user_email}"

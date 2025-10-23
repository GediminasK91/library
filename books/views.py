from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.conf import settings
from .models import Book, BookLoan
from .msal_auth import build_msal_app, get_sign_in_flow
import datetime
from django.shortcuts import render, get_object_or_404

def print_qr(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'books/print_qr.html', {'book': book})
def login_view(request):
    flow = get_sign_in_flow()
    request.session['auth_flow'] = flow
    return redirect(flow['auth_uri'])

def auth_callback(request):
    cache = None
    result = build_msal_app(cache).acquire_token_by_authorization_code(
        request.GET['code'],
        ['User.Read'],
        redirect_uri=settings.MSAL_REDIRECT_URI
    )
    if 'id_token_claims' in result:
        claims = result['id_token_claims']
        username = claims['preferred_username']
        user, created = User.objects.get_or_create(username=username, defaults={
            'first_name': claims.get('given_name', ''),
            'last_name': claims.get('family_name', ''),
            'email': username,
            'is_active': True
        })
        login(request, user)
        return redirect('book_list')
    return HttpResponse("Authentication failed", status=401)

def book_list(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        if title and author:
            Book.objects.create(title=title, author=author)
        return redirect('book_list')

    books = Book.objects.all()
    loans = BookLoan.objects.filter(returned_at__isnull=True)
    loaned_books = {loan.book_id for loan in loans}
    loan_info = {loan.book_id: loan for loan in loans}
    return render(request, 'books/book_list.html', {
        'books': books,
        'loaned_books': loaned_books,
        'loan_info': loan_info
    })

def take_book_page(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    active_loan = BookLoan.objects.filter(book=book, returned_at__isnull=True).first()
    return render(request, "books/take_book.html", {"book": book, "active_loan": active_loan})

def take_book_action(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    active_loan = BookLoan.objects.filter(book=book, returned_at__isnull=True).first()
    if active_loan:
        return render(request, "books/take_book_reserved.html", {
            "message": "Sorry, this book is already taken!"
        })
    if request.user.is_authenticated:
        user_email = request.user.email
    else:
        user_email = "anonymous@example.com"
    BookLoan.objects.create(book=book, user_email=user_email)
    return render(request, "books/take_book_reserved.html", {
        "message": "Your book has been reserved!"
    })

def return_book(request, book_id):
    active_loan = BookLoan.objects.filter(book_id=book_id, returned_at__isnull=True).first()
    if active_loan:
        active_loan.returned_at = datetime.datetime.now()
        active_loan.save()
    return redirect('book_list')

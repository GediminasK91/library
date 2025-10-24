from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
import msal

from .models import Book, BookLoan


# ---------------------------------------------------------------------
# MSAL (Microsoft Entra ID / Azure AD) Inline Configuration
# ---------------------------------------------------------------------

TENANT = (getattr(settings, "MSAL_TENANT_ID", "") or "common").strip()
AUTHORITY = f"https://login.microsoftonline.com/{TENANT}"
SCOPES = ["User.Read"]  # Do NOT include reserved scopes like openid/profile/offline_access


def build_msal_app(cache=None):
    """Builds the MSAL confidential client app."""
    return msal.ConfidentialClientApplication(
        client_id=settings.MSAL_CLIENT_ID,
        client_credential=settings.MSAL_CLIENT_SECRET,
        authority=AUTHORITY,
        token_cache=cache,
    )


def get_sign_in_flow():
    """
    Starts sign-in flow with PKCE.
    IMPORTANT: We must reuse this same 'flow' object on callback.
    """
    app = build_msal_app()
    return app.initiate_auth_code_flow(
        scopes=SCOPES,
        redirect_uri=settings.MSAL_REDIRECT_URI,  # must exactly match Azure config
        prompt="select_account",
    )


# ---------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------

def print_qr(request, book_id):
    """Display printable QR page for a given book."""
    book = get_object_or_404(Book, id=book_id)
    return render(request, "books/print_qr.html", {"book": book})


def login_view(request):
    """
    Redirect user to Microsoft login page.
    Saves the MSAL 'flow' in session so PKCE code_verifier can be used at callback.
    """
    flow = get_sign_in_flow()
    request.session["auth_flow"] = flow  # keep this for callback
    return redirect(flow["auth_uri"])


def auth_callback(request):
    """
    Handle Microsoft OAuth2 redirect callback.

    MUST use acquire_token_by_auth_code_flow(flow, request.GET) with the SAME 'flow'
    saved in session during login_view(), otherwise PKCE will fail with AADSTS50148.
    """
    flow = request.session.get("auth_flow")
    if not flow:
        return HttpResponse("Session expired or invalid auth flow. Please try signing in again.", status=400)

    app = build_msal_app()
    try:
        # This call validates state, exchanges code, and uses the PKCE verifier inside 'flow'
        result = app.acquire_token_by_auth_code_flow(flow, request.GET)
    except ValueError as e:
        # MSAL raises ValueError if state mismatch or other validation error
        return HttpResponse(f"Authentication error: {e}", status=400)
    finally:
        # Remove the flow so it can't be replayed
        request.session.pop("auth_flow", None)

    if "id_token_claims" in result:
        claims = result["id_token_claims"]
        username = claims.get("preferred_username") or claims.get("email")
        if not username:
            return HttpResponse("No username/email returned by Microsoft.", status=400)

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": claims.get("given_name", ""),
                "last_name": claims.get("family_name", ""),
                "email": username,
                "is_active": True,
            },
        )
        login(request, user)
        return redirect("book_list")

    # If token acquisition failed, MSAL returns an error dict instead of id_token_claims
    error_desc = result.get("error_description") or result.get("error") or "Authentication failed"
    return HttpResponse(error_desc, status=401)


@login_required
def book_list(request):
    """
    Main page: list books, show loan info, allow adding new books.
    Now supports text-based owner field (name + surname).
    """
    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        owner_name = request.POST.get("owner")  # now text

        if title and author:
            Book.objects.create(title=title, author=author, owner=owner_name)
        return redirect("book_list")

    q = request.GET.get("q", "").strip()
    books = Book.objects.all()
    if q:
        books = books.filter(
            Q(title__icontains=q) | Q(author__icontains=q) | Q(owner__icontains=q)
        )

    loans = BookLoan.objects.filter(returned_at__isnull=True)
    loaned_books = {loan.book_id for loan in loans}
    loan_info = {loan.book_id: loan for loan in loans}

    return render(
        request,
        "books/book_list.html",
        {
            "books": books,
            "loaned_books": loaned_books,
            "loan_info": loan_info,
            "q": q,
        },
    )


def take_book_page(request, book_id):
    """Show details for taking a specific book."""
    book = get_object_or_404(Book, id=book_id)
    active_loan = BookLoan.objects.filter(book=book, returned_at__isnull=True).first()
    return render(request, "books/take_book.html", {"book": book, "active_loan": active_loan})


@login_required
@require_POST
def take_book_action(request, book_id):
    """Reserve a book for the current logged-in user."""
    book = get_object_or_404(Book, id=book_id)
    with transaction.atomic():
        active_loan = (
            BookLoan.objects.select_for_update()
            .filter(book=book, returned_at__isnull=True)
            .first()
        )
        if active_loan:
            return render(
                request,
                "books/take_book_reserved.html",
                {"message": "Sorry, this book is already taken!"},
            )
        BookLoan.objects.create(book=book, user_email=request.user.email)
    return render(
        request,
        "books/take_book_reserved.html",
        {"message": "Your book has been reserved!"},
    )


@login_required
@require_POST
def return_book(request, book_id):
    """Mark a book as returned."""
    with transaction.atomic():
        active_loan = (
            BookLoan.objects.select_for_update()
            .filter(book_id=book_id, returned_at__isnull=True)
            .first()
        )
        if active_loan:
            active_loan.returned_at = timezone.now()
            active_loan.save(update_fields=["returned_at"])
    return redirect("book_list")

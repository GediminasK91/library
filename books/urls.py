from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Main pages
    path("", views.book_list, name="book_list"),
    path("take/<int:book_id>/", views.take_book_page, name="take_book_page"),
    path("take/<int:book_id>/reserve/", views.take_book_action, name="take_book_action"),
    path("return/<int:book_id>/", views.return_book, name="return_book"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("callback/", views.auth_callback, name="auth_callback"),

    # ✅ QR code route — serves QR stored in DB
    path("qr/<int:book_id>.png", views.book_qr_from_db, name="book_qr_from_db"),

    # Printable QR page
    path("print_qr/<int:book_id>/", views.print_qr, name="print_qr"),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('take/<int:book_id>/', views.take_book_page, name='take_book_page'),
    path('take/<int:book_id>/reserve/', views.take_book_action, name='take_book_action'),
    path('return/<int:book_id>/', views.return_book, name='return_book'),
    path('login/', views.login_view, name='login'),
    path('auth/callback/', views.auth_callback, name='auth_callback'),
    path('print_qr/<int:book_id>/', views.print_qr, name='print_qr'),
]

from django.urls import path
from .views import AuthAPIView, LogoutAPIView

urlpatterns = [
    # Ham Register, ham Login uchun yagona API nuqtasi
    path('', AuthAPIView.as_view(), name='api-auth'),

    # Tizimdan chiqish (Logout) uchun API nuqtasi
    path('logout/', LogoutAPIView.as_view(), name='api-logout'),
]
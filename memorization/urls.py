from django.urls import path
from .views import QueryMemorizationAPIView, test_memorization

urlpatterns = [
    # Link nomlari aslicha qoldi, faqat Klass ko'rinishida chaqirildi
    path("query_memorization/", QueryMemorizationAPIView.as_view()),
    path("test_memorization/", test_memorization),
]
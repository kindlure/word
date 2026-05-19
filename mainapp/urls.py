from django.urls import path
from . import views
from .query_essential import QueryEssentialAPIView
from .test_essential import TestEssentialAPIView
from .result import QuizResultAPIView

urlpatterns = [
    # ==========================================================
    # 1. FRONTEND: BRAUZERDA HTML ANDOZALARNI OCHUVCHI MANZILLAR
    # ==========================================================
    path('home_page/', views.home_page, name='home'),
    path('4000_essential_english_words/', views.essential_english_words, name='essential-books'),
    path('settings/', views.settings, name='settings'),
    path('about/', views.about, name='about'),
    path('play_again/', views.play_again, name='play-again'),

    # Biz izlayotgan va keshda 404 berayotgan HTML sahifaning yangi va to'g'ri manzili:
    path('select_essential/', views.select_essential_page, name='select-essential-page'),

    # Test topshirish HTML sahifasi
    path('test_essential_page/', views.test_essential_page, name='test-essential-page'),

    # ==========================================================
    # 2. BACKEND: FAQAT JAVASCRIPT (FETCH) UCHUN API NUQTALARI
    # ==========================================================
    path('api/query_essential/', QueryEssentialAPIView.as_view(), name='query-essential-api'),
    path('api/test_essential/', TestEssentialAPIView.as_view(), name='test-essential-api'),
    path('api/result/', QuizResultAPIView.as_view(), name='quiz-result-api'),
]
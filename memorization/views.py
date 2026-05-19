from django.utils import timezone
from django.shortcuts import render  # HTML render qilish uchun kerak
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from mainapp.models import Book
from userapp.models import Profil
from .models import Memorization


class QueryMemorizationAPIView(APIView):
    # API faqat tizimga kirgan foydalanuvchilar uchun ishlaydi
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Mavjud kitoblar ro'yxatini va foydalanuvchining joriy yodlash sozlamalarini olish.",
        responses={200: "Kitoblar ro'yxeti va foydalanuvchi ma'lumotlari"}
    )
    def get(self, request):
        # 1. Agar foydalanuvchida Memorization obyekti bo'lmasa, avtomatik yaratamiz
        memorization_obj, created = Memorization.objects.get_or_create(
            profil__user=request.user,
            defaults={'profil': Profil.objects.get(user=request.user)}
        )

        # 2. Kitoblar ro'yxatini shakllantirish
        books = Book.objects.all().values('id', 'name')

        data = {
            "success": True,
            "current_settings": {
                "book": memorization_obj.book_id if memorization_obj.book else None,
                "unit": memorization_obj.unit,
                "language": memorization_obj.language if hasattr(memorization_obj, 'language') else "eng-uzb"
            },
            "available_books": list(books)
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Testni boshlashdan oldin Kitob, Unit va Til sozlamalarini o'rnatish (Saqlash).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'book': openapi.Schema(type=openapi.TYPE_INTEGER, description="Kitob ID raqami (1-6)", default=1),
                'unit': openapi.Schema(type=openapi.TYPE_INTEGER, description="Unit raqami (1-30)", default=1),
                'language': openapi.Schema(type=openapi.TYPE_STRING, description="Test turi: 'eng-uzb' yoki 'uzb-eng'",
                                           default="eng-uzb"),
            },
            required=['book', 'unit', 'language']
        ),
        responses={
            200: "Sozlamalar muvaffaqiyatli saqlandi va testga ruxsat berildi",
            400: "Xato ma'lumot kiritildi (Validatsiya xatoligi)"
        }
    )
    def post(self, request):
        # Data-larni olish
        book_id = request.data.get("book")
        unit = request.data.get("unit")
        language = request.data.get("language")

        # Ma'lumotlar mavjudligini tekshirish
        if book_id is None or unit is None or language is None:
            return Response(
                {"success": False, "message": "book, unit va language maydonlari majburiy!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            book_id = int(book_id)
            unit = int(unit)
            language = str(language)
        except ValueError:
            return Response(
                {"success": False, "message": "Formatlar noto'g'ri kiritildi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # === VALIDATSIYA (Tekshirishlar) ===
        if unit < 1:
            return Response({"success": False, "message": "Unit cannot be less than 1"},
                            status=status.HTTP_400_BAD_REQUEST)
        if unit > 30:
            return Response({"success": False, "message": "The number of unit should not exceed 30"},
                            status=status.HTTP_400_BAD_REQUEST)
        if book_id < 1:
            return Response({"success": False, "message": "Book cannot be less than 1"},
                            status=status.HTTP_400_BAD_REQUEST)
        if book_id > 6:
            return Response({"success": False, "message": "The number of book should not exceed 6"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Foydalanuvchi profilini va oxirgi aktivligini yangilash
        try:
            profil = Profil.objects.get(user=request.user)
            profil.last_activity = timezone.now()
            profil.save()
        except Profil.DoesNotExist:
            return Response({"success": False, "message": "Profil topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # Kitob bazada borligini tekshirish
        if not Book.objects.filter(id=book_id).exists():
            return Response({"success": False, "message": f"IDsi {book_id} bo'lgan kitob topilmadi"},
                            status=status.HTTP_404_NOT_FOUND)

        # Memorization modelini yangilash
        Memorization.objects.filter(profil__user=request.user).update(
            unit=unit,
            book_id=book_id,
            question_lar="[]",
            question_soz=None,
            amount_number=0
        )

        return Response({
            "success": True,
            "message": "Sozlamalar muvaffaqiyatli saqlandi. Endi test API endpointsga so'rov yuborishingiz mumkin.",
            "next_step_url": "/api/quiz/eng-uzb/ yoki /api/quiz/uzb-eng/"
        }, status=status.HTTP_200_OK)


# ==========================================
# Eski funksiyangiz o'z joyiga qaytarildi:
# ==========================================
def test_memorization(request):
    """
    Test sahifasi HTML shablonini ko'rsatish funksiyasi
    """
    return render(request, "test_memorization.html")
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from userapp.models import Profil
from .models import Amount, Word, Soz


class QuizResultAPIView(APIView):
    # API faqat tizimga kirgan foydalanuvchilar uchun ishlaydi
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Foydalanuvchining test natijalarini hisoblash, profil statistikasini yangilash va xato qilingan so'zlar ro'yxatini JSON formatda qaytarish API nuqtasi.",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli hisoblangan natijalar",
                examples={
                    "application/json": {
                        "amount": 20,
                        "language": "eng-uzb",
                        "acceptance": 15,
                        "percentage": 75.0,
                        "mistakes": [
                            "Apple - Olma",
                            "Book - Kitob"
                        ],
                        "description": "Brother Ibrohimov is your result:"
                    }
                }
            ),
            404: "Foydalanuvchi profili yoki test ma'lumotlari topilmadi"
        }
    )
    def get(self, request):
        user = request.user

        # 1. Profil va Amount obyektlarini olish
        try:
            profil = Profil.objects.get(user=user)
            amo = Amount.objects.get(profil__user=user)
        except (Profil.DoesNotExist, Amount.DoesNotExist):
            return Response(
                {"error": "Profil yoki test sozlamalari (Amount) topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Onlayn vaqtini yangilash
        profil.last_activity = timezone.now()

        # 2. Profil statistikasini yangilash
        profil.test += amo.amount
        profil.acceptance += amo.acceptance

        # Profil umumiy foizini hisoblash (percentage)
        whole = profil.acceptance + profil.rejection
        if profil.acceptance != 0 and whole != 0:
            profil.percentage = (profil.acceptance * 100) // whole
        else:
            profil.acceptance = 0
        profil.save()

        # 3. question_lar ro'yxatini xavfsiz o'qish (eval o'rniga json.loads xavfsizroq)
        try:
            question_lar = json.loads(amo.question_lar) if isinstance(amo.question_lar, str) else amo.question_lar
            if not isinstance(question_lar, list):
                question_lar = eval(amo.question_lar)
        except Exception:
            question_lar = []

        mistakes_list = set()

        # 4. Xato qilingan so'zlarni aniqlash (Optimallashgan qism)
        # Zip orqali juftliklarni olamiz: [word_id, 't', word_id, 'f'...] -> (word_id, 't'), (word_id, 'f')
        for x, y in zip(question_lar[::2], question_lar[1::2]):
            if y == "f":  # Agar javob False (xato) bo'lsa
                try:
                    if amo.language == "eng-uzb":
                        # x bu yerda Word ID si. Select_related yoki filter orqali optimal olish
                        word_obj = Word.objects.get(id=x)
                        soz_obj = Soz.objects.filter(word=word_obj).first()
                        soz_name = soz_obj.name if soz_obj else "Tarjima yo'q"
                        mistakes_list.add(f"{word_obj.name} - {soz_name}")
                    else:
                        # x bu yerda Soz ID si (uzb-eng testida)
                        soz_obj = Soz.objects.select_related('word').get(id=x)
                        mistakes_list.add(f"{soz_obj.name} - {soz_obj.word.name}")
                except Exception:
                    # Agar bazadan o'chib ketgan so'z bo'lsa xato bermasligi uchun
                    continue

        # 5. Jinsga qarab tavsif matni (Description)
        if profil.gender == "male":
            description = f"Brother {profil.name} is your result:"
        else:
            description = f"Sister {profil.name} is your result:"

        # Joriydagi test foizini hisoblash (Aprel oyi aniqligida // va / amallari bilan)
        try:
            current_percentage = (amo.acceptance * 100) / amo.amount
            current_percentage = round(current_percentage, 1) # Chiroyli ko'rinishi uchun masalan 75.5
        except ZeroDivisionError:
            current_percentage = 0

        # 6. JSON ma'lumotlarni qaytarish
        data = {
            "amount": amo.amount,
            "language": amo.language,
            "acceptance": amo.acceptance,
            "percentage": current_percentage,
            "mistakes": list(mistakes_list), # Swagger va Front-end qabul qilishi uchun list holatiga o'tkazildi
            "description": description,
        }

        return Response(data, status=status.HTTP_200_OK)
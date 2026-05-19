import random
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Memorization, Soz, Word, Error


class UzbEngQuizAPIView(APIView):
    # API faqat tizimga kirgan foydalanuvchilar uchun ishlaydi
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="O'zbekcha-Inglizcha so'z yodlash testi uchun unit diapazoni bo'yicha tasodifiy savol va variantlar generatsiya qilish API nuqtasi.",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli savol generatsiya qilindi",
                examples={
                    "application/json": {
                        "soz_id": 45,
                        "soz_name": "Olma",
                        "soz_0": "Apple",
                        "soz_1": "Book",
                        "soz_2": "Pen",
                        "amount": 10,
                        "acceptance": 5,
                        "amount_number": 1.5
                    }
                }
            ),
            404: "Foydalanuvchiga tegishli yodlash ma'lumotlari topilmadi"
        }
    )
    def get(self, request):
        # 1. Foydalanuvchining Memorization obyektini olish
        amount_queryset = Memorization.objects.filter(profil__user=request.user)

        if not amount_queryset.exists():
            return Response(
                {"error": "Yodlash ma'lumotlari topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        memorization_obj = amount_queryset.first()
        from_u = memorization_obj.from_unit
        to_u = memorization_obj.to_unit

        # Maxsimal so'zlar sonini hisoblash
        if to_u - from_u == 0:
            amo = 20
        else:
            amo = (to_u - from_u) * 20

        # 2. question_lar ro'yxatini xavfsiz parslash
        try:
            question_lar = json.loads(memorization_obj.question_lar) if isinstance(memorization_obj.question_lar,
                                                                                   str) else memorization_obj.question_lar
            if not isinstance(question_lar, list):
                question_lar = eval(memorization_obj.question_lar)
        except Exception:
            question_lar = []

        length = len(question_lar)
        couple = length // 6
        q_s = None

        # 3. Algoritm bo'yicha so'z (Soz id-si) tanlash
        while True:
            random_soz = Soz.objects.filter(
                word__unit__range=(from_u, to_u),
                word__book=memorization_obj.book
            ).order_by('?').first()

            if not random_soz:
                return Response({"error": "Belgilangan unitlarda so'zlar topilmadi"},
                                status=status.HTTP_400_BAD_REQUEST)

            current_q_s = random_soz.id

            # Xato qilingan so'zlarni qayta chiqarish tekshiruvi
            if couple >= 1 and length >= 6:
                if question_lar[length - 5] == 'f':
                    q_s = question_lar[length - 6]
                    amount_queryset.update(question_soz=q_s)
                    break
            if couple >= 2 and length >= 12:
                if question_lar[length - 11] == 'f':
                    q_s = question_lar[length - 12]
                    amount_queryset.update(question_soz=q_s)
                    break

            # Bitta chiqqan so'z qaytib chiqmasligi yoki limit tugaganligi sharti
            if current_q_s not in question_lar or amo < memorization_obj.amount_number:
                q_s = current_q_s
                amount_queryset.update(question_soz=q_s)
                break
            else:
                try:
                    ind = question_lar.index(current_q_s)
                    if question_lar[::-1][ind + 1] == "f":
                        q_s = current_q_s
                        amount_queryset.update(question_soz=q_s)
                        break
                except Exception:
                    pass

        # 4. Tanlangan Soz obyektini olish
        try:
            soz_object = Soz.objects.get(id=q_s)
        except Soz.DoesNotExist:
            return Response({"error": "Tanlangan o'zbekcha so'z topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # 5. Inglizcha variantlar ro'yxatini shakllantirish (Word modelidan)
        all_responses = [word.name for word in Word.objects.filter(
            unit__range=(from_u, to_u),
            book=memorization_obj.book
        ).order_by('?')[:3]]

        while len(all_responses) < 3:
            all_responses.append("—")

        data = {
            "soz_0": all_responses[0],
            "soz_1": all_responses[1],
            "soz_2": all_responses[2],
        }

        # 6. To'g'ri javobni variantlar ichiga tekshirib joylash
        try:
            right_translation = soz_object.word.name
        except Exception:
            right_translation = "Translation missing"

        if right_translation not in all_responses:
            keys = list(data.keys())
            right_key = random.choice(keys)
            data[right_key] = right_translation

        # 7. Progressni yangilash (amount_number ni 0.5 ga oshirish)
        amount_queryset.update(amount_number=F('amount_number') + 0.5)

        # Yangilangan qiymatni response'da to'g'ri ko'rsatish uchun qayta yuklaymiz
        memorization_obj.refresh_from_db()

        # 8. Yakuniy ma'lumotlarni yig'ish
        data['soz_id'] = soz_object.id
        data['soz_name'] = soz_object.name  # O'zbekcha so'z nomi (Savol)
        data['amount'] = memorization_obj.amount
        data['acceptance'] = memorization_obj.acceptance
        data['amount_number'] = memorization_obj.amount_number

        return Response(data, status=status.HTTP_200_OK)
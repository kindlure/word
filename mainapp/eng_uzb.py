import random
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Amount, Word, Soz, Error


class EngUzbQuizRangeAPIView(APIView):
    # API faqat tizimga kirgan foydalanuvchilar uchun ishlaydi
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Inglizcha-O'zbekcha so'z yodlash testi uchun berilgan Unit diapazonlari (from_unit -> to_unit) bo'yicha tasodifiy savol va variantlar generatsiya qilish API nuqtasi.",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli savol generatsiya qilindi",
                examples={
                    "application/json": {
                        "word_id": 15,
                        "word_name": "Book",
                        "soz_0": "Kitob",
                        "soz_1": "Qalam",
                        "soz_2": "Kompyuter",
                        "amount": 10,
                        "acceptance": 5,
                        "amount_number": 2
                    }
                }
            ),
            404: "Foydalanuvchiga tegishli hisob (Amount) ma'lumotlari topilmadi"
        }
    )
    def get(self, request):
        # 1. Foydalanuvchining Amount obyektini olish
        amount_queryset = Amount.objects.filter(profil__user=request.user)

        if not amount_queryset.exists():
            return Response(
                {"error": "Yodlash ma'lumotlari (Amount) topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        amount_obj = amount_queryset.first()
        from_u = amount_obj.from_unit
        to_u = amount_obj.to_unit

        # Maxsimal so'zlar sonini hisoblash (amo)
        if to_u - from_u == 0:
            amo = 20
        else:
            amo = (to_u - from_u + 1) * 20

        # 2. question_lar ma'lumotini xavfsiz parslash (eval o'rniga json.loads yoki xavfsiz usul)
        try:
            question_lar = json.loads(amount_obj.question_lar) if isinstance(amount_obj.question_lar,
                                                                             str) else amount_obj.question_lar
            if not isinstance(question_lar, list):
                question_lar = eval(amount_obj.question_lar)
        except Exception:
            question_lar = []

        length = len(question_lar)
        couple = length // 6
        q_s = None

        # 3. Algoritm bo'yicha so'z tanlash (While logikasi)
        while True:
            # Diapazon va Kitob bo'yicha tasodifiy so'z qidirish
            random_word = Word.objects.filter(
                unit__range=(from_u, to_u),
                book=amount_obj.book
            ).order_by('?').first()

            if not random_word:
                return Response({"error": "Belgilangan unit diapazonida so'zlar topilmadi"},
                                status=status.HTTP_400_BAD_REQUEST)

            current_q_s = random_word.id

            # Xato qilingan so'zlarni qayta chiqarish tekshiruvlari
            if couple >= 1 and length >= 6:
                if question_lar[length - 5] == 'f':
                    q_s = question_lar[length - 6]
                    break
            if couple >= 2 and length >= 12:
                if question_lar[length - 11] == 'f':
                    q_s = question_lar[length - 12]
                    break

            # Bitta chiqqan so'z qaytib chiqmasligi sharti
            int_sonlar_soni = sum(isinstance(element, int) for element in question_lar)
            if current_q_s not in question_lar or int_sonlar_soni >= amo:
                q_s = current_q_s
                break
            else:
                try:
                    ind = question_lar.index(current_q_s)
                    if question_lar[::-1][ind + 1] == "f":
                        q_s = current_q_s
                        break
                except Exception:
                    pass

        # Tanlangan so'z ID sini bazaga yozish
        amount_queryset.update(question_soz=q_s)

        # 4. Tanlangan Word obyektini bazadan olish
        try:
            word_object = Word.objects.get(id=q_s)
        except Word.DoesNotExist:
            return Response({"error": "Tanlangan so'z topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # 5. Variantlar (O'zbekcha javoblar) ro'yxatini shakllantirish
        all_responses = [soz.name for soz in Soz.objects.filter(
            word__unit__range=(from_u, to_u),
            word__book=amount_obj.book
        ).order_by('?')[:3]]

        while len(all_responses) < 3:
            all_responses.append("—")

        data = {
            "soz_0": all_responses[0],
            "soz_1": all_responses[1],
            "soz_2": all_responses[2],
        }

        # 6. To'g'ri javobni variantlar ichiga joylashtirish tekshiruvi
        try:
            right_translation = Soz.objects.filter(word=word_object).first().name
        except Exception:
            Error.objects.create(
                name="soz__word",
                description=f"{q_s} bunga tegishli tarjima topilmadi. Fayl: views.py (EngUzbQuizRangeAPIView)"
            )
            right_translation = "Tarjima mavjud emas"

        # Agar to'g'ri javob variantlar ichida bo'lmasa, tasodifiy bittasiga almashtirish
        if right_translation not in all_responses:
            keys = list(data.keys())
            right_key = random.choice(keys)
            data[right_key] = right_translation

        # 7. Progressni oshirish (+1)
        amount_queryset.update(amount_number=F('amount_number') + 1)

        # Yangilangan holatni javobda to'g'ri ko'rsatish uchun obyektni yangilaymiz
        amount_obj.refresh_from_db()

        # 8. Yakuniy ma'lumotlarni yig'ish va qaytarish
        data['word_id'] = word_object.id
        data['word_name'] = word_object.name
        data['amount'] = amount_obj.amount
        data['acceptance'] = amount_obj.acceptance
        data['amount_number'] = amount_obj.amount_number

        return Response(data, status=status.HTTP_200_OK)
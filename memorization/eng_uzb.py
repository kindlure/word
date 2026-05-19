import random
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Memorization, Word, Soz, Error


class EngUzbQuizAPIView(APIView):
    # API faqat tizimga kirgan (login bo'lgan) foydalanuvchilar uchun ishlaydi
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Inglizcha-O'zbekcha so'z yodlash testi uchun tasodifiy savol va 3 ta variant variant generatsiya qilish API nuqtasi.",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli savol generatsiya qilindi",
                examples={
                    "application/json": {
                        "word_id": 12,
                        "word_name": "Apple",
                        "soz_0": "Olma",
                        "soz_1": "Kitob",
                        "soz_2": "Ruchka",
                        "amount": 10,
                        "acceptance": 5,
                        "amount_number": 1
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
                {"error": "Yodlash ma'lumotlari topilmadi. Avval profil sozlamalarini tekshiring."},
                status=status.HTTP_404_NOT_FOUND
            )

        memorization_obj = amount_queryset.first()

        # 2. question_lar ma'lumotini xavfsiz parslash (eval o'rniga json.loads yoki xavfsiz usul)
        try:
            question_lar = json.loads(memorization_obj.question_lar) if isinstance(memorization_obj.question_lar,
                                                                                   str) else memorization_obj.question_lar
            if not isinstance(question_lar, list):
                question_lar = eval(memorization_obj.question_lar)  # Eski format saqlanib qolgan bo'lsa
        except Exception:
            question_lar = []

        length = len(question_lar)
        couple = length // 6
        q_s = None

        # 3. Algoritm bo'yicha so'z tanlash (While logikasi)
        while True:
            # Tasodifiy bitta so'z id sini olish
            random_word = Word.objects.filter(book=memorization_obj.book).order_by('?').first()
            if not random_word:
                return Response({"error": "Kitob ichida so'zlar topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

            current_q_s = random_word.id

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

            # Bitta chiqqan so'z qaytib chiqmasligi sharti
            if current_q_s not in question_lar:
                q_s = current_q_s
                amount_queryset.update(question_soz=q_s)
                break
            else:
                try:
                    top = question_lar
                    ind = top.index(current_q_s)
                    if top[::-1][ind + 1] == "f":
                        q_s = current_q_s
                        amount_queryset.update(question_soz=q_s)
                        break
                except Exception:
                    pass

        # 4. Tanlangan Word obyektini bazadan olish
        try:
            word_object = Word.objects.get(id=q_s)
        except Word.DoesNotExist:
            return Response({"error": "Tanlangan so'z bazadan topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # 5. Variantlar (Javoblar) ro'yxatini shakllantirish
        all_responses = [soz.name for soz in Soz.objects.filter(word__book=memorization_obj.book).order_by('?')[:3]]

        # Agar variantlar 3 tadan kam bo'lsa, xatolik bermasligi uchun himoya
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
                description=f"{q_s} bunga tegishli tarjima topilmadi. Fayl: views.py (EngUzbQuizAPIView)"
            )
            right_translation = "Tarjima mavjud emas"

        # Agar to'g'ri javob variantlar ichida bo'lmasa, tasodifiy bittasiga almashtirish
        if right_translation not in all_responses:
            keys = list(data.keys())
            right_key = random.choice(keys)
            data[right_key] = right_translation

        # 7. Yakuniy JSON ma'lumotlarni yig'ish va qaytarish
        data['word_id'] = word_object.id
        data['word_name'] = word_object.name  # Swagger va Front-end uchun qulay bolishi uchun string formatda
        data['amount'] = memorization_obj.amount
        data['acceptance'] = memorization_obj.acceptance
        data['amount_number'] = memorization_obj.amount_number

        return Response(data, status=status.HTTP_200_OK)
import json
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from userapp.models import Profil
from .models import Amount, Word, Soz

# DIQQAT: eng_uzb va uzb_eng funksiyalarini loyihangizga moslab chaqiring yoki ichki metod qiling.
# Quyidagi kodda ularning mantiqi funksiya sifatida chaqiriladi.
from .eng_uzb import EngUzbQuizRangeAPIView
from .uzb_eng import uzb_eng


class TestEssentialAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Navbatdagi test savolini olish (GET so'rovi). Agar testlar soni tugagan bo'lsa, avtomatik ravishda tugaganlik haqida xabar beradi.",
        responses={
            200: openapi.Response(
                description="Navbatdagi savol ma'lumotlari",
                examples={
                    "application/json": {
                        "is_finished": False,
                        "error_dictionary": "Apple - Olma (Agar oldingi savolda xato qilingan bo'lsa chiqadi)",
                        "word_name": "Book",
                        "soz_0": "Kitob",
                        "soz_1": "Qalam",
                        "soz_2": "Kompyuter",
                        "amount_number": 3,
                        "amount": 20
                    }
                }
            ),
            400: "Sozlamalar yoki profil topilmadi"
        }
    )
    def get(self, request):
        user = request.user

        # Profil va vaqtni yangilash
        try:
            profil = Profil.objects.get(user=user)
            profil.last_activity = timezone.now()
            profil.save()
            amount_queryset = Amount.objects.filter(profil__user=user)
            amount_obj = amount_queryset.first()
        except (Profil.DoesNotExist, AttributeError, IndexError):
            return Response({"error": "Foydalanuvchi ma'lumotlari topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

        if not amount_obj:
            return Response({"error": "Avval sozlamalarni (Amount) o'rnating"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Testlar soni tugaganligini tekshirish
        if amount_obj.amount < amount_obj.amount_number:
            return Response({
                "is_finished": True,
                "message": "Test yakunlandi. Natijalar sahifasiga o'ting.",
                "redirect_url": "/result/"
            }, status=status.HTTP_200_OK)

        # 2. Agar oldingi savol xato bo'lsa, ekranga chiroyli lug'at (Error dictionary) chiqarish
        try:
            question_lar = json.loads(amount_obj.question_lar) if isinstance(amount_obj.question_lar,
                                                                             str) else amount_obj.question_lar
            if not isinstance(question_lar, list):
                question_lar = eval(amount_obj.question_lar)
        except Exception:
            question_lar = []

        error_word_detail = None
        if question_lar and question_lar[-1] == "f":
            last_failed_id = question_lar[-2]
            try:
                if amount_obj.language == "eng-uzb":
                    w_obj = Word.objects.get(id=last_failed_id)
                    s_obj = Soz.objects.filter(word=w_obj).first()
                    error_word_detail = f"""{w_obj.name} - {s_obj.name if s_obj else "Tarjima yo'q"}"""
                elif amount_obj.language == "uzb-eng":
                    s_obj = Soz.objects.get(id=last_failed_id)
                    error_word_detail = f"{s_obj.name} - {s_obj.word.name}"
            except Exception:
                pass

        # 3. Til yo'nalishiga qarab navbatdagi savolni generatsiya qilish
        data = {"is_finished": False, "error_dictionary": error_word_detail}

        if amount_obj.language == "eng-uzb":
            # eng_uzb funksiyasi dictionary qaytarishi kerak (Sizning kodingiz bo'yicha)
            generated_question = EngUzbQuizRangeAPIView(request)
            data.update(generated_question)
        elif amount_obj.language == "uzb-eng":
            generated_question = uzb_eng(request)
            data.update(generated_question)

        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Foydalanuvchi tanlagan javobni qabul qilish va tekshirish (POST so'rovi).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'soz': openapi.Schema(type=openapi.TYPE_STRING,
                                      description="Foydalanuvchi bosgan variant matni (Javob)", default="Kitob")
            },
            required=['soz']
        ),
        responses={
            200: "Javob muvaffaqiyatli qabul qilindi. Navbatdagi savolga o'tish uchun GET so'rovini yuboring.",
            400: "Xato ma'lumot yuborildi"
        }
    )
    def post(self, request):
        user = request.user
        chosen_answer = request.data.get('soz')

        if not chosen_answer:
            return Response({"error": "Javob ('soz' maydoni) yuborilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        # Foydalanuvchi sozlamalarini olish
        amount_queryset = Amount.objects.filter(profil__user=user)
        amount_obj = amount_queryset.first()

        if not amount_obj:
            return Response({"error": "Test sozlamalari topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        # Tarix ro'yxatini yuklash
        try:
            question_lar_1 = json.loads(amount_obj.question_lar) if isinstance(amount_obj.question_lar,
                                                                               str) else amount_obj.question_lar
            if not isinstance(question_lar_1, list):
                question_lar_1 = eval(amount_obj.question_lar)
        except Exception:
            question_lar_1 = []

        q_s = amount_obj.question_soz

        # === 1-HOLAT: INGLIZCHA -> O'ZBEKCHA TEKSHIRUV ===
        if amount_obj.language == "eng-uzb":
            # Foydalanuvchi tanlagan variant to'g'riligini tekshirish
            respons = list(Soz.objects.filter(name=chosen_answer).values_list('word__name', flat=True))

            try:
                current_word_name = Word.objects.get(id=q_s).name
                is_correct = current_word_name in respons
            except Word.DoesNotExist:
                is_correct = False

            if is_correct:
                amount_queryset.update(acceptance=F('acceptance') + 1)
                question_lar_1.extend([q_s, "t"])
            else:
                Profil.objects.filter(user=user).update(rejection=F('rejection') + 0.5)
                question_lar_1.extend([q_s, "f"])

            amount_queryset.update(question_lar=str(question_lar_1))

        # === 2-HOLAT: O'ZBEKCHA -> INGLIZCHA TEKSHIRUV ===
        elif amount_obj.language == "uzb-eng":
            try:
                correct_word_name = Soz.objects.get(id=q_s).word.name
                is_correct = (chosen_answer == correct_word_name)
            except Soz.DoesNotExist:
                is_correct = False

            if is_correct:
                amount_queryset.update(acceptance=F('acceptance') + 1)
                question_lar_1.extend([q_s, "t"])
            else:
                Profil.objects.filter(user=user).update(rejection=F('rejection') + 0.5)
                question_lar_1.extend([q_s, "f"])

            amount_queryset.update(question_lar=str(question_lar_1))

        return Response({
            "success": True,
            "message": "Javob yozildi. Navbatdagi savolni olish uchun GET so'rovini amalga oshiring."
        }, status=status.HTTP_200_OK)
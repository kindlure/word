from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from userapp.models import Profil
from .models import Amount


# --- 1. VALIDATSIYA VA MA'LUMOTLAR FORMATI UCHUN SERIALIZER ---
class QueryEssentialSerializer(serializers.Serializer):
    book = serializers.IntegerField(default=1, min_value=1)
    from_unit = serializers.IntegerField(default=1, min_value=0)
    to_unit = serializers.IntegerField(default=30, min_value=1)
    amount = serializers.IntegerField(default=5, min_value=1, max_value=250)
    language = serializers.ChoiceField(choices=['eng-uzb', 'uzb-eng'], default='eng-uzb')

    # Biznes mantiq (Kross-field) validatsiyasi
    def validate(self, attrs):
        from_unit = attrs.get('from_unit')
        to_unit = attrs.get('to_unit')

        if from_unit > to_unit:
            raise serializers.ValidationError({
                "message": "There is no word between these numbers (From Unit To Unit dan katta bo'lishi mumkin emas)."
            })
        return attrs


# --- 2. ASOSIY API VIEW ---
class QueryEssentialAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Foydalanuvchining joriy Amount (test oraliqlari va kitob) sozlamalarini ko'rish. "
                              "Agar obyekt bo'lmasa, default qiymatlar bilan avtomatik yaratiladi.",
        responses={200: "Joriy sozlamalar muvaffaqiyatli yuklandi"}
    )
    def get(self, request):
        try:
            profil = Profil.objects.get(user=request.user)
        except Profil.DoesNotExist:
            return Response(
                {"success": False, "message": "Foydalanuvchi profili topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obyekt bo'lsa oladi, bo'lmasa default qiymatlar bilan ochadi
        amount_obj, created = Amount.objects.get_or_create(
            profil=profil,
            defaults={
                'book': 1,
                'from_unit': 1,
                'to_unit': 30,
                'amount': 5,
                'language': 'eng-uzb',
                'amount_number': 1,
                'acceptance': 0,
                'question_lar': "[]"
            }
        )

        # Agar eski obyekt bo'lsa, testni boshidan boshlash uchun uning progresslarini tozalaymiz
        if not created:
            Amount.objects.filter(profil=profil).update(amount_number=1, acceptance=0, question_lar="[]")
            amount_obj.refresh_from_db()

        return Response({
            "success": True,
            "current_settings": {
                "book": amount_obj.book,
                "from_unit": amount_obj.from_unit,
                "to_unit": amount_obj.to_unit,
                "amount": amount_obj.amount,
                "language": amount_obj.language,
                "amount_number": amount_obj.amount_number,
                "acceptance": amount_obj.acceptance
            }
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Kitob, unitlar oralig'i, testlar soni va til sozlamalarini saqlash.",
        request_body=QueryEssentialSerializer,  # Swaggerni serializerga bog'ladik
        responses={
            200: "Sozlamalar muvaffaqiyatli saqlandi",
            400: "Validatsiya xatoligi yuz berdi"
        }
    )
    def post(self, request):
        # Ma'lumotlarni serializer orqali qat'iy tekshiramiz
        serializer = QueryEssentialSerializer(data=request.data)

        if not serializer.is_valid():
            # Xatolik matnini chiroyli formatda yig'ib frontendlga qaytaramiz
            error_msg = "Validatsiya xatoligi yuz berdi."
            if 'non_field_errors' in serializer.errors:
                error_msg = serializer.errors['non_field_errors'][0]
            elif 'message' in serializer.errors:
                error_msg = serializer.errors['message'][0]
            else:
                # Birinchi duch kelgan maydon xatoligini olish
                first_field = list(serializer.errors.keys())[0]
                error_msg = f"{first_field}: {serializer.errors[first_blue][0]}" if 'first_blue' in locals() else f"{first_field} noto'g'ri kiritildi."

            return Response(
                {"success": False, "message": error_msg, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Profilni olish va oxirgi aktivlikni yangilash
        try:
            profil = Profil.objects.get(user=request.user)
            profil.last_activity = timezone.now()
            profil.save()
        except Profil.DoesNotExist:
            return Response({"success": False, "message": "Profil topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        validated_data = serializer.validated_data

        # Ma'lumotlarni bazada xavfsiz saqlash (Obyekt bor bo'lsa yangilaydi, yo'q bo'lsa yaratadi)
        Amount.objects.update_or_create(
            profil=profil,
            defaults={
                "book": validated_data['book'],
                "amount": validated_data['amount'],
                "from_unit": validated_data['from_unit'],
                "to_unit": validated_data['to_unit'],
                "language": validated_data['language'],
                "question_lar": "[]",
                "amount_number": 1,
                "acceptance": 0
            }
        )

        return Response({
            "success": True,
            "message": "Sozlamalar muvaffaqiyatli saqlandi. Endi testga o'tishingiz mumkin.",
            "next_step_url": "/test_essential/"
        }, status=status.HTTP_200_OK)
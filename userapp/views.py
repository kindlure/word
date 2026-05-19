from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from mainapp.models import Profil
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import urllib.parse


class AuthAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Foydalanuvchini ro'yxatdan o'tkazish (Register) yoki Tizimga kirish (Login). "
                              "Parametrlarni URL orqali (?username=...) yoki JSON Body orqali yuborish mumkin.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Foydalanuvchi nomi (Majburiy)"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Parol (Majburiy)"),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Ism (Faqat Register uchun)"),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, description="Jinsi (Faqat Register uchun)"),
                'year_of_birth': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                description="Tug'ilgan yili (Faqat Register uchun)"),
            },
            required=['username', 'password']
        ),
        responses={
            200: "Muvaffaqiyatli login/register bajarildi",
            400: "Xato ma'lumot yuborildi yoki Username band",
            401: "Login yoki Parol xato"
        }
    )
    def post(self, request):
        # 1. URL ichidagi parametrlarni tekshirish (Sizning eski uslubingiz uchun)
        url = request.get_full_path()
        query = urllib.parse.urlparse(url).query
        url_params = dict(urllib.parse.parse_qsl(query))

        # 2. Ma'lumotlarni ham URLdan, ham JSON Body'dan yig'ib olish (Kombinatsiya)
        username = request.data.get('username') or url_params.get('username')
        password = request.data.get('password') or url_params.get('password')
        name = request.data.get('name') or url_params.get('name')
        gender = request.data.get('gender') or url_params.get('gender')
        year_of_birth = request.data.get('year_of_birth') or url_params.get('year_of_birth')

        if not username or not password:
            return Response(
                {"error": "Username va password maydonlari majburiy!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # === REGISTER LOGIKASI ===
        if name:
            try:
                user = User.objects.create_user(username=username, password=password)
                Profil.objects.create(
                    name=name,
                    gender=gender,
                    year_of_birth=year_of_birth,
                    user=user
                )
                login(request, user)
                return Response({
                    "status": "success",
                    "message": "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi va tizimga kirdi.",
                    "user": {"username": user.username, "name": name}
                }, status=status.HTTP_201_CREATED)

            except IntegrityError:
                return Response(
                    {"error": "Bu username allaqachon mavjud."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # === LOGIN LOGIKASI ===
        else:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return Response({
                    "status": "success",
                    "message": "Tizimga muvaffaqiyatli kirildi."
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Username yoki password xato!"},
                    status=status.HTTP_401_UNAUTHORIZED
                )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Tizimdan chiqish (Logout)",
        responses={200: "Tizimdan muvaffaqiyatli chiqildi"}
    )
    def post(self, request):
        logout(request)
        return Response({
            "status": "success",
            "message": "Tizimdan muvaffaqiyatli chiqildi."
        }, status=status.HTTP_200_OK)
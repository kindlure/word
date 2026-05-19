from django.contrib import admin
from django.urls import path, include
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
schema_view = get_schema_view(
   openapi.Info(
      title="Word memorization API",
      default_version='v1',
      description="The most addictive learn to new word and spelling trivia quiz word game ever! It’s proven fact that learning new things in proper way helps you remember things quickly and for long-term! Word_Memorization is a new educational English memorizing a new word game that will check and improve your Vocabulary skills in an entertaining and challenging way!",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact("Ikromjon Ibrohimov: kindlure1234@gmail.com"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],)

urlpatterns = [
    path('admin_panel/', admin.site.urls),
    path('', include('userapp.urls')),
    path('', include('mainapp.urls')),
    path('', include('memorization.urls')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0)),
]




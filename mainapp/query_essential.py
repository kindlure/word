from django.shortcuts import render, redirect
import json
from django.http import JsonResponse
from django.utils import timezone
from .models import Amount, Profil  # O'zingizning modellaringiz nomi

def query_post(request):
    # 1. Kelgan JSON ma'lumotni o'qib olamiz
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Noto'g'ri ma'lumot formati"}, status=400)

    # 2. Ma'lumotlarni o'zgaruvchilarga olamiz
    book = int(data.get("book", 1))
    from_unit = int(data.get("from_unit", 0))
    to_unit = int(data.get("to_unit", 0))
    amount = int(data.get("amount", 0))
    language = str(data.get("language", "eng-uzb"))

    # 3. Profil faolligini yangilaymiz
    profil = Profil.objects.get(user=request.user)
    profil.last_activity = timezone.now()
    profil.save()

    # 4. Tekshirishlar (Validation)
    if from_unit < 0:
        return JsonResponse({"success": False, "message": "Unit cannot be less than 0"})
    if to_unit < 1:
        return JsonResponse({"success": False, "message": "Unit cannot be less than 1"})
    elif from_unit > to_unit:
        return JsonResponse({"success": False, "message": "There is no word between these numbers"})
    if amount < 1:
        return JsonResponse({"success": False, "message": "Number of tests cannot be less than 0"})
    elif amount > 250:
        return JsonResponse({"success": False, "message": "The number of tests should not exceed 250"})

    # 5. Ma'lumotlar bazasini yangilaymiz
    Amount.objects.filter(profil__user=request.user).update(
        amount=amount,
        from_unit=from_unit,
        to_unit=to_unit,
        language=language,
        book=book,          # Yangi kelayotgan book raqamini ham saqlaymiz
        amount_number=1,  # 👈 BU JUDA MUHIM! Test hisoblagichini 1 dan boshlaymiz
        acceptance=0,  # 👈 BU HAM MUHIM! To'g'ri javoblarni 0 qilamiz
        question_lar="[]"
    )

    # 6. HTML JS kodi kutayotgan muvaffaqiyatli JSON javobini qaytaramiz
    return JsonResponse({
        "success": True,
        "message": "Settings saved successfully!",
        "next_step_url": "/test_essential/"  # JS avtomat shu sahifaga o'tkazadi
    })

def query_essential_1(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            return query_post(request=request)
        try:
            Amount.objects.get(profil__user=request.user)
        except:
            Amount.objects.create(profil=Profil.objects.get(user=request.user), book=1)
        else:
            Amount.objects.filter(profil__user=request.user).update(amount_number=1, acceptance=0, question_lar="[]", book=1)
        return render(request, "query_essential.html", {"success": True})
    return redirect('/')

def query_essential_2(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            return query_post(request=request)
        try:
            Amount.objects.get(profil__user=request.user)
        except:
            Amount.objects.create(profil=Profil.objects.get(user=request.user), book=1)
        else:
            Amount.objects.filter(profil__user=request.user).update(amount_number=1, acceptance=0, question_lar="[]", book=2)
        return render(request, "query_essential.html", {"success": True})
    return redirect('/')

def query_essential_3(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            return query_post(request=request)
        try:
            Amount.objects.get(profil__user=request.user)
        except:
            Amount.objects.create(profil=Profil.objects.get(user=request.user), book=1)
        else:
            Amount.objects.filter(profil__user=request.user).update(amount_number=1, acceptance=0, question_lar="[]", book=3)
        return render(request, "query_essential.html", {"success": True})
    return redirect('/')
"""
amount_model_id = 1     # model ID si


"""
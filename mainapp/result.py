from django.shortcuts import render, redirect
from .models import *
from userapp.models import Profil
from django.utils import timezone

def result_f(request):
    if request.user.is_authenticated:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()

        # (rejection) sonini (test_1_essential) da qo'shib ketyapti.
        # Profilga har result qilinganda (test), (acceptance) sonini oshirish uchun:
        amo = Amount.objects.get(profil__user=request.user)
        pr = Profil.objects.get(user=request.user)
        pr.test += amo.amount
        pr.acceptance += amo.acceptance

        # Profilga har result qilinganda (percentage) ini o'zgartirish uchun:
        whole = pr.acceptance + pr.rejection
        pr.percentage = pr.acceptance * 100 / whole * 1000 // 1000

        pr.save()

        # Resultda Xato qilgan so'zlari chiqarish uchun:
        question_lar = eval(amo.question_lar)
        mistakes_list = set()
        for x, y in zip(question_lar[::2], question_lar[1::2]):
            if y == "f":  # f ya'ni False Xato topgani, t True to'g'ri topgani.
                if amo.language == "eng-uzb":
                    mistakes_list.add(f"{Word.objects.get(id=x).name} - {Soz.objects.filter(word=x)[0].name}")
                else:
                    soz = Soz.objects.get(id=x)
                    mistakes_list.add(f"{soz.name} - {soz.word.name}")
        if pr.gender == "male":
            description = f"Brother {pr.name} is your result:"
        else:
            description = f"Sister {pr.name} is your result:"
        data = {"amount": amo.amount,
                "language": amo.language,
                "acceptance": amo.acceptance,
                "percentage": amo.acceptance * 100 / amo.amount * 1000 // 1000,
                "mistakes": mistakes_list,
                "description": description, }
        return render(request, "result.html", data)
    return redirect('/')
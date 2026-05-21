from django.shortcuts import render, redirect
from .models import *
from userapp.models import Profil
from .eng_uzb import eng_uzb_f
from .uzb_eng import uzb_eng_f
from django.db.models import F
from django.utils import timezone

def test_essential_f(request):
    if request.user.is_authenticated:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()

        if request.method == "POST":
            amount = Amount.objects.filter(profil__user=request.user)
            if amount[0].language == "eng-uzb":
                soz = request.POST.get('soz')
                if soz:
                    # respons = Soz.objects.filter(name=soz)[0]
                    respons = list(Soz.objects.filter(name=soz).values_list('word__name', flat=True))
                    q_s = amount[0].question_soz

                    question_lar_1 = eval(amount[0].question_lar)

                    if Word.objects.get(id=q_s).name in respons:
                        amount.update(acceptance=F('acceptance') + 1)

                        # Har bir testni {q_s: "t") ya'ni qaysi so'zni topgan topmaganini yozib ketadi
                        question_lar_1.append(q_s)
                        question_lar_1.append("t")
                        amount.update(question_lar=f"{question_lar_1}")
                    else:
                        Profil.objects.filter(user=request.user).update(rejection=F('rejection') + 0.5)

                        # Har bir testni {q_s: "f") ya'ni qaysi so'zni topgan topmaganini yozib ketadi
                        question_lar_1.append(q_s)
                        question_lar_1.append("f")
                        amount.update(question_lar=f"{question_lar_1}")
                # eng_uzb(request=request)

            elif amount[0].language == "uzb-eng":
                soz = request.POST.get('soz')
                if soz:
                    q_s = amount[0].question_soz

                    question_lar_1 = eval(amount[0].question_lar)

                    if soz == Soz.objects.get(id=q_s).word.name:
                        amount.update(acceptance=F('acceptance') + 1)

                        # Har bir testni {q_s: "t") ya'ni qaysi so'zni topgan topmaganini yozib ketadi
                        question_lar_1.append(q_s)
                        question_lar_1.append("t")
                        amount.update(question_lar=f"{question_lar_1}")
                    else:
                        Profil.objects.filter(user=request.user).update(rejection=F('rejection') + 0.5)

                        # Har bir testni {q_s: "f") ya'ni qaysi so'zni topgan topmaganini yozib ketadi
                        question_lar_1.append(q_s)
                        question_lar_1.append("f")
                        amount.update(question_lar=f"{question_lar_1}")
                # uzb_eng(request=request)

        # Agar testlar soni marta test yechib bo'lgan bo'lsa o'yinni tugatish uchun:
        amount = Amount.objects.filter(profil__user=request.user)
        if amount[0].amount < amount[0].amount_number:
            return redirect('/result/')

        # agar belgilagan testi xato bo'lsa Lug'at chiqishi uchun:
        question_lar = eval(amount[0].question_lar)
        data = {"error": False}
        if question_lar:
            if question_lar[-1] == "f":
                data = {"error": question_lar[-2]}

        if amount[0].language == "eng-uzb":
            if data["error"]:
                data["error"] = f"{Word.objects.get(id=data['error']).name} - {Soz.objects.filter(word=Word.objects.get(id=data['error']))[0].name}"
            data.update(eng_uzb_f(request=request))
            return render(request, "test_essential.html", data)

        elif amount[0].language == "uzb-eng":
            if data["error"]:
                data["error"] = f"{Soz.objects.get(id=data['error']).name} - {Soz.objects.filter(id=data['error'])[0].word.name}"
            data.update(uzb_eng_f(request=request))
            return render(request, "test_essential.html", data)

    return redirect('/')


"""
number = Amount.objects.get(id=amount_model_id).amount_number
Amount.objects.get(id=amount_model_id).update(amount_number=number + 1)
print(Soz.objects.get(name=request.POST.get("soz")).word.name, question_soz.name, "1_POST")

return render(request, "test_essential.html", {"word": language, "soz": language})

number = Amount.objects.get(id=amount_model_id).amount_number
Amount.objects.get(id=amount_model_id).update(amount_number=number + 1)
print(Soz.objects.get(name=request.POST.get("soz")).word.name, question_soz.name, "1_POST")
"""
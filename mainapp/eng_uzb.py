from .models import *
import random
from django.db.models import F

def eng_uzb_f(request):
    # Cheklangan from_unit dan boshlanib to_unit gacha bo'lgan Unitdagi so'zlarni topish uchun:
    amount = Amount.objects.filter(profil__user=request.user)
    from_u = amount[0].from_unit
    to_u = amount[0].to_unit

    question_lar = eval(amount[0].question_lar)
    length = len(question_lar)
    couple = length // 6
    if to_u - from_u == 0:      amo = 20
    else:                       amo = (to_u - from_u + 1) * 20
    while 1:
        q_s = Word.objects.filter(unit__range=(from_u, to_u), book=amount[0].book).order_by('?').first().id

        # Test davomida Xato qilgan so'zi har 2 ta so'zdan keyin qayta 2 marta chiqishi kerak,
        #    agar, keyingi chiqqanda ham xato qilsa yana keyingilarda 2 marta chiqishi kerak:
        if couple >= 1:
            if question_lar[length - 5] == 'f':
                q_s = question_lar[length - 6]
                break
        if couple >= 2:
            if question_lar[length - 11] == 'f':
                q_s = question_lar[length - 12]
                break

        # Bitta chiqqan so'z qaytib chiqmasligi uchun, agar to'g'ri javobini topgan bo'lsa:
        int_sonlar_soni = sum(isinstance(element, int) for element in question_lar)
        if q_s not in question_lar or int_sonlar_soni >= amo:
            break
        else:
            ind = question_lar.index(q_s)
            if question_lar[::-1][ind + 1] == "f":
                break
    amount.update(question_soz=q_s)

    # Har hil javoblarni chiqarish uchun:
    all_respons = [soz.name for soz in
                         Soz.objects.filter(word__unit__range=(from_u, to_u), word__book=amount[0].book).order_by('?')[:3]]
    data = {"soz_0": all_respons[0],
            "soz_1": all_respons[1],
            "soz_2": all_respons[2], }

    # Bu shart variantlar orasida to'g'ri javob 2 ta bo'lib qolmasligi uchun.
    try:
        Soz.objects.filter(word=Word.objects.get(id=q_s))[0].name
    except:
        Error.objects.create(name="soz__word", description=f"{q_s} bunga tegishli (Soz.objects.filter(word=Word.objects.get(id=q_s))[0].name) shu kodda xato bor fayl: (eng-uzb.py) 54 lines")
    response = Soz.objects.filter(word=Word.objects.get(id=q_s))[0].name

    if response != all_respons[0] and response != all_respons[1] and response != all_respons[2]:
        keys = list(data.keys())
        right_1 = random.choice(keys)
        data[right_1] = Soz.objects.filter(word=Word.objects.get(id=q_s))[0].name

    data['word'] = Word.objects.get(id=q_s)
    data['amount'] = amount[0].amount
    data['acceptance'] = amount[0].acceptance
    data['amount_number'] = amount[0].amount_number

    amount.update(amount_number=F('amount_number') + 1)
    return data


"""

"""
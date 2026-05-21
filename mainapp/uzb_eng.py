from .models import *
import random
from django.db.models import F

def uzb_eng_f(request):

    # Cheklangan from_unit dan boshlanib to_unit gacha bo'lgan Unitdagi so'zlarni topish uchun:
    amount = Amount.objects.filter(profil__user=request.user)
    from_u = amount[0].from_unit
    to_u = amount[0].to_unit

    if to_u - from_u == 0:  amo = 20
    else:                   amo = (to_u - from_u +1) * 20
    question_lar = eval(amount[0].question_lar)
    length = len(question_lar)
    couple = length // 6

    int_sonlar_soni = sum(isinstance(element, int) for element in question_lar)
    while_11 = 0
    while 1:
        q_s = Soz.objects.filter(word__unit__range=(from_u, to_u), word__book=amount[0].book).order_by('?').first().id

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
        if int_sonlar_soni <= amo:
            if q_s not in question_lar:
                break

        while_11 += 1
        print("While OPEN", amo, int_sonlar_soni, couple, q_s, question_lar, while_11)
    print("While CLOSE", while_11)

    amount.update(question_soz=q_s)

    # Har hil javoblarni chiqarish uchun:
    all_respons = [soz.name for soz in
                         Word.objects.filter(unit__range=(from_u, to_u), book=amount[0].book).order_by('?')[:3]]
    data = {"soz_0": all_respons[0],
            "soz_1": all_respons[1],
            "soz_2": all_respons[2], }

    # Bu shart variantlar orasida to'g'ri javob 2 ta bo'lib qolmasligi uchun.
    response = Soz.objects.filter(id=q_s)[0].word.name
    if response != all_respons[0] and \
            response != all_respons[1] and \
            response != all_respons[2]:
        keys = list(data.keys())
        right_1 = random.choice(keys)
        data[right_1] = Soz.objects.get(id=q_s).word

    data['word'] = Soz.objects.get(id=q_s)
    data['amount'] = amount[0].amount
    data['acceptance'] = amount[0].acceptance
    data['amount_number'] = amount[0].amount_number

    amount.update(amount_number=F('amount_number') + 1)
    return data


"""
    # if q_s not in question_lar or \
    #         amo < Amount.objects.get(profil__user=request.user).amount_number:
    #     amount.update(question_soz=q_s)
    #     break
    # else:
    #     ind = question_lar.index(q_s)
    #     if question_lar[::-1][ind + 1] == "f":
    #         amount.update(question_soz=q_s)
    #         break
"""
import random
import json
from django.db.models import F
from .models import Amount, Word, Soz


def uzb_eng(request):
    """
    O'zbekcha-Inglizcha test uchun tasodifiy savol va variantlarni generatsiya qiluvchi funksiya.
    """
    # 1. Foydalanuvchining Amount sozlamalarini olish
    amount_queryset = Amount.objects.filter(profil__user=request.user)
    if not amount_queryset.exists():
        return {}

    amount_obj = amount_queryset.first()
    from_u = amount_obj.from_unit
    to_u = amount_obj.to_unit

    # Maksimal testlar sonini aniqlash (amo)
    if to_u - from_u == 0:
        amo = 20
    else:
        amo = (to_u - from_u + 1) * 20

    # 2. question_lar ro'yxatini xavfsiz o'qish
    try:
        question_lar = json.loads(amount_obj.question_lar) if isinstance(amount_obj.question_lar,
                                                                         str) else amount_obj.question_lar
        if not isinstance(question_lar, list):
            question_lar = eval(amount_obj.question_lar)
    except Exception:
        question_lar = []

    length = len(question_lar)
    couple = length // 6
    int_sonlar_soni = sum(isinstance(element, int) for element in question_lar)

    q_s = None
    loop_counter = 0  # Cheksiz tsikl (Infinite loop) dan himoya qilish uchun

    # 3. Savol tanlash logikasi (While tsikli)
    while loop_counter < 100:  # Maksimal 100 marta urinish (bazani qotirib qo'ymaslik uchun)
        loop_counter += 1

        # Diapazondagi tasodifiy o'zbekcha so'z (Soz id si) ni olish
        random_soz = Soz.objects.filter(
            word__unit__range=(from_u, to_u),
            word__book=amount_obj.book
        ).order_by('?').first()

        if not random_soz:
            break

        current_q_s = random_soz.id

        # Xato qilingan so'zlarni qayta chiqarish (Sizning algoritmingiz)
        if couple >= 1 and length >= 6:
            if question_lar[length - 5] == 'f':
                q_s = question_lar[length - 6]
                break
        if couple >= 2 and length >= 12:
            if question_lar[length - 11] == 'f':
                q_s = question_lar[length - 12]
                break

        # Bitta chiqqan so'z qaytib chiqmasligi sharti
        if int_sonlar_soni <= amo:
            if current_q_s not in question_lar:
                q_s = current_q_s
                break
        else:
            # Agar hamma so'zlar chiqib bo'lgan bo'lsa, joriy so'zni qabul qilamiz
            q_s = current_q_s
            break

    # Agar tsiklda muammo bo'lsa va q_s topilmasa, default oxirgisini olish
    if not q_s and random_soz:
        q_s = random_soz.id

    # Tanlangan savol ID sini saqlash
    amount_queryset.update(question_soz=q_s)

    # 4. Variantlarni (Inglizcha so'zlarni) shakllantirish
    all_respons = [word.name for word in Word.objects.filter(
        unit__range=(from_u, to_u),
        book=amount_obj.book
    ).order_by('?')[:3]]

    # Agar bazada so'z yetarli bo'lmasa, xato bermasligi uchun to'ldirish
    while len(all_respons) < 3:
        all_respons.append("—")

    data = {
        "soz_0": all_respons[0],
        "soz_1": all_respons[1],
        "soz_2": all_respons[2],
    }

    # 5. To'g'ri javob variantlar ichida borligini tekshirish
    try:
        soz_object = Soz.objects.select_related('word').get(id=q_s)
        response_word_name = soz_object.word.name
    except Soz.DoesNotExist:
        return {}

    if response_word_name not in all_respons:
        keys = list(data.keys())
        right_key = random.choice(keys)
        data[right_key] = response_word_name

    # 6. Yakuniy ma'lumotlarni yig'ish (Swagger va Front-end tushunadigan toza matn va ID lar)
    data['word_id'] = soz_object.id
    data['word_name'] = soz_object.name  # O'zbekcha so'z (Savol)
    data['amount'] = amount_obj.amount
    data['acceptance'] = amount_obj.acceptance
    data['amount_number'] = amount_obj.amount_number

    # Progressni bittaga oshirish
    amount_queryset.update(amount_number=F('amount_number') + 1)

    return data
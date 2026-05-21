from django.shortcuts import render, redirect
from django.utils import timezone
from userapp.models import Profil

def error(request, exception=None):
    return render(request, "error.html", status=404)


def home_page(request):
    if not request.user.is_authenticated:
        return redirect('/')
    try:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()
        return render(request, "home_page.html", {"name": profil.name})
    except Profil.DoesNotExist:
        return redirect('/')


def essential_english_words(request):
    if not request.user.is_authenticated:
        return redirect('/')
    try:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()
        return render(request, "essential_english_words.html")
    except Profil.DoesNotExist:
        return redirect('/')


def select_essential_page(request):
    """
    Kitob tanlangandan keyin ochiladigan sozlamalar sahifasi.
    Sizning papkangizda bu andoza 'query_essential.html' deb nomlangan.
    """
    if not request.user.is_authenticated:
        return redirect('/')
    try:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()
        return render(request, "query_essential.html")  # Real faylingiz nomi ulandi!
    except Profil.DoesNotExist:
        return redirect('/')


def test_essential_page(request):
    """ Test savollari ko'rinadigan HTML sahifani render qilish """
    if not request.user.is_authenticated:
        return redirect('/')
    try:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()
        return render(request, "test_essential.html")   # Papkangizdagi real fayl
    except Profil.DoesNotExist:
        return redirect('/')


def play_again(request):
    if request.user.is_authenticated:
        return redirect('/select_essential/')  # 🚀 To'g'ridan-to'g'ri URL manzilini yozamiz (boshiga va oxiriga / qo'ying)
    return redirect('/')


def settings(request):
    if not request.user.is_authenticated:
        return redirect('/')
    try:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()

        if request.method == "POST":
            profil.name = request.POST.get("name")
            profil.tel_number = request.POST.get('tel_number')
            profil.year_of_birth = request.POST.get('year_of_birth')
            profil.save()
            return redirect('/home_page/')

        if profil.test != 0:
            return render(request, "settings.html", {"i": profil})
        return render(request, "settings.html", {"i": profil, "p": "You haven't taken the test yet"})
    except Profil.DoesNotExist:
        return redirect('/')


def about(request):
    if not request.user.is_authenticated:
        return redirect('/')
    try:
        profil = Profil.objects.get(user=request.user)
        profil.last_activity = timezone.now()
        profil.save()
        return render(request, "about.html")
    except Profil.DoesNotExist:
        return redirect('/')
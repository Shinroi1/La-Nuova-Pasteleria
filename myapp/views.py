import json
import random
from collections import Counter
from .decorators import allowed_users
from datetime import datetime, timezone
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate,logout
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.utils.timezone import make_aware
from django.contrib import messages
from django.conf import settings
from django.db.models import F, ExpressionWrapper, DurationField
from django.db.models import Count, Q
from django.contrib.auth.models import Group
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.views import PasswordChangeView
from .models import Menu, NormalReservationTable, NormalReservationOrder, SessionDishHistory, UnavailableDateTime
from .forms import AdminRegisterForm, MenuForm, NormalReservationForm, AdminProfileForm, UnavailableDateTimeForm

# from django.http import HttpResponse
# from django.utils.encoding import force_str
# from django.http import HttpResponseRedirect
# from django.urls import reverse

def test(request):
    return render(request, "test.html")

# View to render user navigation bar
def user_navbar(request):
    
    return render(request, "user_navbar.html", {'user': request.user})

def chatbot(request):
    # Render the chatbot template
    return render(request, "chatbot.html")

# Render home view with proper recommendations
def home(request):
    cookies_accepted = check_cookie_consent(request)

    # Step 1: Check for cookie consent
    if cookies_accepted:
        # Step 2: If user has history, show personalized recommendations
        personalized_recs = get_similar_dishes(request)
        print(f"Personalized Recommendations:", list(personalized_recs))  # Debugging output

        if personalized_recs.exists():
            context = {
                'dishes': personalized_recs, 
                'personalized': True,
                'cookies_accepted': True}
        else:
            print("Fallback to bestsellers: No personalized dishes found.")
            top_dishes = get_global_bestsellers()
            context = {
                'dishes': top_dishes, 
                'personalized': False,
                'cookies_accepted': True}

    else:
        top_dishes = get_global_bestsellers()
        context = {
            'dishes': top_dishes, 
            'personalized': False,
            'cookies_accepted': False}

    return render(request, "home.html", context)
    
# Function to check if the user has given cookie consent
# This function checks if the 'cookie_consent' cookie is set to 'true'.
def check_cookie_consent(request):
    consent = request.COOKIES.get('cookie_consent')
    return consent == 'true'

# Function to get collaborative recommendations based on session history
# This function retrieves dishes that similar users have ordered, excluding the user's own history.
def get_collaborative_recommendations(request):
    session_key = request.session.session_key

    if not session_key:
        print("[Collaborative] No session key, returning random dishes.")
        return Menu.objects.order_by('?')[:6], True  # True = is_random

    user_dish_ids = SessionDishHistory.objects.filter(session_key=session_key).values_list('dish_id', flat=True)
    if not user_dish_ids.exists():
        print("[Collaborative] No user dish history found, returning random dishes.")
        return Menu.objects.order_by('?')[:6], True

    similar_sessions = SessionDishHistory.objects.filter(
        dish_id__in=user_dish_ids
    ).exclude(session_key=session_key).values_list('session_key', flat=True).distinct()

    recommended_dish_ids = SessionDishHistory.objects.filter(
        session_key__in=similar_sessions
    ).exclude(dish_id__in=user_dish_ids) \
     .values('dish_id').annotate(count=Count('dish_id')).order_by('-count')[:6]

    recommended_ids = [d['dish_id'] for d in recommended_dish_ids]
    if not recommended_ids:
        print("[Collaborative] No recommendations found, returning random dishes.")
        return Menu.objects.order_by('?')[:6], True

    print(f"[Collaborative] Recommended Dish IDs: {recommended_ids}")
    return Menu.objects.filter(id__in=recommended_ids), False  # False = not random


# View to recommend alternatives based on collaborative filtering
# This view will be called when the user clicks on the "Recommend Alternatives" button.
def recommend_alternatives(request):
    recommended_dishes, is_random = get_collaborative_recommendations(request)

    if is_random:
        heading = "HWe couldn't find your usual favorites — but no worries! Here's something to spark your appetite:"
    else:
        heading = "Other customers also ordered these:"

    data = [
        {
            'name': dish.dish_name,
            'category': dish.category,
            'slug': dish.slug,
            'image_url': static(dish.image) if dish.image else static("images/default.jpg"),
            'description': dish.ingredients,
            'price': float(dish.price)
        }
        for dish in recommended_dishes
    ]

    print(f"Recommended Dishes (collaborative): {data}")
    return JsonResponse({'dishes': data, 'heading': heading})
 
# Function to store user's dish history in session
# This function will be called when the user selects dishes.
def store_user_dish_history(request, selected_dishes):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    print(f"Session: {request.session.session_key}")
    print(f"Session Key: {session_key}")
    print(f"Selected Dishes: {selected_dishes}")  # Debugging output

    for dish_id, dish_data in selected_dishes.items():
        try:
            dish = Menu.objects.get(id=int(dish_id))  # Convert key to int
            SessionDishHistory.objects.create(session_key=session_key, dish=dish)
            print(f"[History] Saved dish {dish.dish_name} for session {session_key}")
        except Menu.DoesNotExist:
            print(f"[History] Dish ID {dish_id} not found in Menu.")
            continue

    # Save to session too (optional, for quick lookup)
    request.session['dish_history'] = selected_dishes

# Function to get similar dishes based on user's dish history
def get_similar_dishes(request, limit=6):
    session_key = request.session.session_key
    if not session_key:
        return Menu.objects.none()

    # Get user's dish history
    user_dishes = SessionDishHistory.objects.filter(session_key=session_key).values_list('dish__id', flat=True)
    user_dish_ids = set(user_dishes)

    if not user_dish_ids:
        return get_global_bestsellers(limit=limit)

    # Gather all other sessions
    others = SessionDishHistory.objects.exclude(session_key=session_key)
    session_map = {}

    for entry in others:
        session_map.setdefault(entry.session_key, []).append(entry.dish.id)

    # Collaborative filtering
    score_counter = Counter()

    for other_dishes in session_map.values():
        overlap = user_dish_ids.intersection(other_dishes)
        score = len(overlap)

        if score > 0:
            for dish_id in other_dishes:
                if dish_id not in user_dish_ids:
                    score_counter[dish_id] += score

    top_ids = [dish_id for dish_id, _ in score_counter.most_common(limit)]
    recommended_dishes = Menu.objects.filter(id__in=top_ids)

    return recommended_dishes


# SHOW UP FOR FIRST TIME VISITORS
def get_global_bestsellers(limit=6):

    dish_counter = Counter()
    orders = NormalReservationOrder.objects.select_related('dish')
    print(f"[DEBUG] Found {orders.count()} orders in NormalReservationOrder")

    for order in orders:
        if order.dish:
            print(f"[DEBUG] Counting dish: {order.dish.id} - {order.dish.dish_name} x {order.quantity}")
            dish_counter[order.dish.id] += order.quantity
        else:
            print(f"[DEBUG] Skipping order with missing dish: {order}")

    if not dish_counter:
        print("[DEBUG] No orders found. Returning random dishes.")
        return Menu.objects.order_by('?')[:limit]

    # Step 1: Dishes ordered 3 or more times
    top_dish_ids = [dish_id for dish_id, total in dish_counter.items() if total >= 3]

    if not top_dish_ids:
        # Step 2: Fallback to dishes ordered at least once (but < 3)
        top_dish_ids = [dish_id for dish_id, total in dish_counter.items() if total >= 1]
        print(f"[DEBUG] Fallback to dish_ids with count < 3: {top_dish_ids}")

    if not top_dish_ids:
        # Step 3: No orders at all — random fallback
        print("[DEBUG] No bestseller data at all. Returning random dishes.")
        return Menu.objects.order_by('?')[:limit]

    # Sort selected dish_ids by popularity (highest first)
    sorted_dish_ids = sorted(top_dish_ids, key=lambda id_: dish_counter[id_], reverse=True)
    print(f"[DEBUG] Final bestseller dish IDs: {sorted_dish_ids[:limit]}")
    
    return Menu.objects.filter(id__in=sorted_dish_ids[:limit])

# USED FOR BESTSELLERS BUTTON
def get_bestsellers(request):
    # bestsellers = get_global_bestsellers(limit=6)

    all_bestsellers = list(get_global_bestsellers(limit=100))  # Larger pool after filter
    random.shuffle(all_bestsellers)  # Shuffle so each click gives new batch
    bestsellers = all_bestsellers[:6]  # Only send 6 dishes
    
    data = [
        {
            'name': dish.dish_name,
            'category': dish.category,
            'slug': dish.slug,
            'image_url': static(dish.image) if dish.image else static("images/default.jpg"),
            'description': dish.ingredients,
            'price': float(dish.price)
        }
        for dish in bestsellers
    ]
    return JsonResponse({'dishes': data})

# Constants for reservation logic (rules based AI for forms)
OPEN_HOUR = 10   # 10 AM
CLOSE_HOUR = 21 # 9 PM
MAX_PARTY_SIZE = 12  # Maximum party size allowed for normal reservations
MIN_ADVANCE_DAY = 1  # Minimum days in advance for reservations

def validate_reservation_data(date, party_size):
    now = make_aware(datetime.now())

    if date < now + timedelta(days=MIN_ADVANCE_DAY):
        return False, f"Reservations must be made at least {MIN_ADVANCE_DAY} day(s) in advance."

    if date.hour < OPEN_HOUR or date.hour >= CLOSE_HOUR:
        return False, "Reservation must be within operating hours (10 AM to 9 PM)."

    if int(party_size) > MAX_PARTY_SIZE:
        return False, f"Maximum party size is {MAX_PARTY_SIZE}."

    if slot_blocked(date):
        return False, "This time slot is unavailable due to exclusive reservations or admin block."

    return True, ""

def slot_blocked(reservation_datetime):
    reservation_date = reservation_datetime.date()
    reservation_time = reservation_datetime.time()

    # Retrieve all unavailable slots for that date
    unavailable_slots = UnavailableDateTime.objects.filter(date=reservation_date)

    for slot in unavailable_slots:
        # Combine slot date and time to get full datetime
        slot_start = datetime.combine(slot.date, slot.start_time)
        slot_end = datetime.combine(slot.date, slot.end_time)

        # Make timezone aware if needed
        slot_start = make_aware(slot_start)
        slot_end = make_aware(slot_end)

        if slot_start <= reservation_datetime <= slot_end:
            return True

    return False


def reservation_form(request):
    if request.method == 'POST':
        form = NormalReservationForm(request.POST)
        selected_dishes_json = request.POST.get('selected_dishes', '{}')  # Preserve selected dishes

        print("Received POST request:", request.POST)

        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        party_size = request.POST.get('party_size')
        total_price = request.POST.get('total_price')
        date_str = request.POST.get('date')

        try:
            date = make_aware(datetime.strptime(date_str, "%Y-%m-%dT%H:%M"))
        except Exception as e:
            return render(request, 'reservation_form.html', {
                'error': 'Invalid date format.',
                'form_data': request.POST,
                'selected_dishes_json': selected_dishes_json,
            })

        is_valid, message = validate_reservation_data(date, party_size)
        if not is_valid:
            return render(request, 'reservation_form.html', {
                'error': message,
                'form_data': request.POST,
                'selected_dishes_json': selected_dishes_json,
            })

        reservation = NormalReservationTable.objects.create(
            fullname=fullname,
            email=email,
            phone=phone,
            party_size=party_size,
            total_price=total_price,
            date=date
        )

        # Save selected dishes to reservation order table
        if selected_dishes_json:
            try:
                selected_dishes = json.loads(selected_dishes_json)
                for dish_id_str, dish_info in selected_dishes.items():
                    try:
                        dish = Menu.objects.get(id=int(dish_id_str))
                        quantity = int(dish_info.get('quantity', 1))
                        NormalReservationOrder.objects.create(
                            reservation=reservation,
                            dish=dish,
                            quantity=quantity
                        )
                    except Menu.DoesNotExist:
                        continue
            except json.JSONDecodeError:
                pass

        # Store user dish history if cookies allowed
        cookie_consent = request.COOKIES.get('cookie_consent')
        if cookie_consent == 'true' and selected_dishes_json:
            try:
                selected_dishes = json.loads(selected_dishes_json)
                store_user_dish_history(request, selected_dishes)
            except json.JSONDecodeError:
                pass

        request.session['reservation_success'] = True
        return redirect('reservation_form')

    success = request.session.pop('reservation_success', False)

    return render(request, 'reservation_form.html', {
        'success': success
    })



# FOR THE MODAL ON THE RESERVATION FORM PAGE
def fetch_dishes(request):
    if request.method == '':
        try:
            dishes = Menu.objects.values('id', 'name')  # Fetch dish id and name
            return JsonResponse({'dishes': list(dishes)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

# FOR THE MODAL ON THE RESERVATION FORM PAGE
@csrf_exempt
def save_dishes(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_dishes = data.get(selected_dishes, [])
        return JsonResponse({'message': 'Dishes saved successfully!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

   
def Calendar(request):
    return render(request, "Calendar.html")

def menu_category(request):
    return render(request, "menu_category.html")

# View to render menu page
def Full_Menu(request):
    return render(request, "Menu/Full Menu.html")

# ANTIPASTI
def Antipasti(request):
    return render(request, "Menu/Antipasti.html")

def Spinach_Trifolate(request):
    return render(request, "Menu/Antipasti/Spinach Trifolate.html")

def Cozze_Ubriachi_Bianco(request):
    return render(request, "Menu/Antipasti/Cozze Ubriachi Bianco.html")

def Parmigiana_Di_Melanzane(request):
    return render(request, "Menu/Antipasti/Parmigiana Di Melanzane.html")

def Prosciutto_Farcito(request):
    return render(request, "Menu/Antipasti/Prosciutto Farcito.html")

def Dita_Di_Pollo_Caprese(request):
    return render(request, "Menu/Antipasti/Dita Di Pollo Caprese.html")

def Molluschi(request):
    return render(request, "Menu/Antipasti/Molluschi.html")

def Prosciutto_Di_Parma_Con_Mango(request):
    return render(request, "Menu/Antipasti/Prosciutto Di Parma Con Mango.html")

def Gamberi_Alla_Griglia(request):
    return render(request, "Menu/Antipasti/Gamberi Alla Griglia.html")

def Salmone_Affucimato(request):
    return render(request, "Menu/Antipasti/Salmone Affucimato.html")

def Calamari_Fritti(request):
    return render(request, "Menu/Antipasti/Calamari Fritti.html")

def Sicilian(request):
    return render(request, "Menu/Antipasti/Sicilian.html")

def Bruschetta_Di_Parma(request):
    return render(request, "Menu/Antipasti/Bruschetta Di Parma.html")

def Bruschetta_Al_Fungo(request):
    return render(request, "Menu/Antipasti/Bruschetta Al Fungo.html")

def Funghi_Ripieni(request):
    return render(request, "Menu/Antipasti/Funghi Ripieni.html")


# INSALATA
def Insalata(request):
    return render(request, "Menu/Insalata.html")

def Caesar(request):
    return render(request, "Menu/Insalata/Caesar.html")

def Mista(request):
    return render(request, "Menu/Insalata/Mista.html")

def Greca(request):
    return render(request, "Menu/Insalata/Greca.html")

def Caprese(request):
    return render(request, "Menu/Insalata/Caprese.html")

def Piccante(request):
    return render(request, "Menu/Insalata/Piccante.html")

def Mare(request):
    return render(request, "Menu/Insalata/Mare.html")


# ZUPPA
def Zuppa(request):
    return render(request, "Menu/Zuppa.html")

def Cippole(request):
    return render(request, "Menu/Zuppa/Cippole.html")

def Vongole(request):
    return render(request, "Menu/Zuppa/Vongole.html")

def Brodetto_Di_Mare(request):
    return render(request, "Menu/Zuppa/Brodetto Di Mare.html")

def Funghi(request):
    return render(request, "Menu/Zuppa/Funghi.html")

def Minestrone_Di_Verdure(request):
    return render(request, "Menu/Zuppa/Minestrone Di Verdure.html")

# PANINI
def Panini(request):
    return render(request, "Menu/Panini.html")

def Rustica(request):
    return render(request, "Menu/Panini/Rustica.html")

def Mortadella(request):
    return render(request, "Menu/Panini/Mortadella.html")

def Pollo(request):
    return render(request, "Menu/Panini/Pollo.html")

def Al_Tono(request):
    return render(request, "Menu/Panini/Al Tono.html")

def Pesce_Filetto(request):
    return render(request, "Menu/Panini/Pesce Filetto.html")

# RISOTTO
def Risotto(request):
    return render(request, "Menu/Risotto.html")

def Porcini(request):
    return render(request, "Menu/Risotto/Porcini.html")

def Marinara(request):
    return render(request, "Menu/Risotto/Marinara.html")

def Colorata(request):
    return render(request, "Menu/Risotto/Colorata.html")


# PIZZA
def Pizza(request):
    return render(request, "Menu/Pizza.html")

def Quattro_Formaggi(request):
    return render(request, "Menu/Pizza/Quattro Formaggi.html")

def Due_Gusti(request):
    return render(request, "Menu/Pizza/Due Gusti.html")

def Margherita(request):
    return render(request, "Menu/Pizza/Margherita.html")

def Pepperoni(request):
    return render(request, "Menu/Pizza/Pepperoni.html")

def La_Loca(request):
    return render(request, "Menu/Pizza/La Loca.html")

def Frutti_Di_Mare(request):
    return render(request, "Menu/Pizza/Frutti Di Mare.html")

def Cacciatora(request):
    return render(request, "Menu/Pizza/Cacciatora.html")

def La_Nuova_Pizza(request):
    return render(request, "Menu/Pizza/La Nuova Pizza.html")

def Tropicale(request):
    return render(request, "Menu/Pizza/Tropicale.html")

def Calzone_Siciliana(request):
    return render(request, "Menu/Pizza/Calzone Siciliana.html") 

# PASTA
def Pasta(request):
    return render(request, "Menu/Pasta.html")

# OLIVE OIL - PASTA
def Vongole_Al_Vino_Bianco(request):
    return render(request, "Menu/Pasta/Olive Oil/Vongole Al Vino Bianco.html")

def Gamberi(request):
    return render(request, "Menu/Pasta/Olive Oil/Gamberi.html")

def Salsiccia(request):
    return render(request, "Menu/Pasta/Olive Oil/Salsiccia.html")

def Misto_De_Pesce(request):
    return render(request, "Menu/Pasta/Olive Oil/Misto De Pesce.html")

def Nera(request):
    return render(request, "Menu/Pasta/Olive Oil/Nera.html")

def Primavera(request):
    return render(request, "Menu/Pasta/Olive Oil/Primavera.html")

def Angulas(request):
    return render(request, "Menu/Pasta/Olive Oil/Angulas.html")

# CREAM - PASTA
def Profumo_Di_Tartufo(request):
    return render(request, "Menu/Pasta/Cream/Profumo Di Tartufo.html")

def Carbonara(request):
    return render(request, "Menu/Pasta/Cream/Carbonara.html")

def Salmone(request):
    return render(request, "Menu/Pasta/Cream/Salmone.html")

def Capesante(request):
    return render(request, "Menu/Pasta/Cream/Capesante.html")

def Chicken_Alfredo(request):
    return render(request, "Menu/Pasta/Cream/Chicken Alfredo.html")

def Ravioli_Funghi(request):
    return render(request, "Menu/Pasta/Cream/Ravioli Funghi.html")

# TOMATO - PASTA
def Bolognese(request):
    return render(request, "Menu/Pasta/Tomato/Bolognese.html")

def Puttanesca(request):
    return render(request, "Menu/Pasta/Tomato/Puttanesca.html")

def Arrabiata(request):
    return render(request, "Menu/Pasta/Tomato/Arrabiata.html")

def Pescatora(request):
    return render(request, "Menu/Pasta/Tomato/Pescatora.html")

def Ravioli_Verde(request):
    return render(request, "Menu/Pasta/Tomato/Ravioli Verde.html")

# PESTO - PASTA
def Conn_Aglio_Olio(request):
    return render(request, "Menu/Pasta/Pesto/Conn Aglio Olio.html")

def Nina(request):
    return render(request, "Menu/Pasta/Pesto/Nina.html")

def Di_Mare(request):
    return render(request, "Menu/Pasta/Pesto/Di Mare.html")

def La_Nuova(request):
    return render(request, "Menu/Pasta/Pesto/La Nuova.html")

def Chorizo(request):
    return render(request, "Menu/Pasta/Pesto/Chorizo.html")

# SECONDI
def Secondi(request):
    return render(request, "Menu/Secondi.html")

# PESCE/FISH
def Al_Forno(request):
    return render(request, "Menu/Secondi/Pesce/Al Forno.html")

def Filetto_Mugnaia(request):
    return render(request, "Menu/Secondi/Pesce/Filetto Mugnaia.html")

def Filetto_Di_Salmon(request):
    return render(request, "Menu/Secondi/Pesce/Filetto Di Salmon.html")

def Grigilia_Di_Pesce(request):
    return render(request, "Menu/Secondi/Pesce/Grigilia Di Pesce.html")

def Cacciuco_Alla_Livornese(request):
    return render(request, "Menu/Secondi/Pesce/Cacciuco Alla Livornese.html")

def Filetto_Spumante(request):
    return render(request, "Menu/Secondi/Pesce/Filetto Spumante.html")

# POLLO/CHICKEN
def Petto_Funghi(request):
    return render(request, "Menu/Secondi/Pollo/Petto Funghi.html")

def Petto_Asparagi(request):
    return render(request, "Menu/Secondi/Pollo/Petto Asparagi.html")

def Petto_Alexi(request):
    return render(request, "Menu/Secondi/Pollo/Petto Alexi.html")

def Accrotolato(request):
    return render(request, "Menu/Secondi/Pollo/Accrotolato.html")

def Petto_Diavola(request):
    return render(request, "Menu/Secondi/Pollo/Petto Diavola.html")

def Cacciatore(request):
    return render(request, "Menu/Secondi/Pollo/Cacciatore.html")

# MANZO/BEEF
def Filetto_Di_Manzo_Ai_Funghi(request):
    return render(request, "Menu/Secondi/Manzo/Filetto Di Manzo Ai Funghi.html")

def Agnello_Alla_Scottadito(request):
    return render(request, "Menu/Secondi/Manzo/Agnello Alla Scottadito.html")

def La_Bistecca(request):
    return render(request, "Menu/Secondi/Manzo/La Bistecca.html")

def Vitello_Alla_Milanese(request):
    return render(request, "Menu/Secondi/Manzo/Vitello Alla Milanese.html")

def Vitello_Al_Marsala(request):
    return render(request, "Menu/Secondi/Manzo/Vitello Al Marsala.html")

def Vitello_Ai_Funghi(request):
    return render(request, "Menu/Secondi/Manzo/Vitello Ai Funghi.html")


# CAFFE
def Caffe(request):
    return render(request, "Menu/Caffe.html")

# CAFFE
def Bevande(request):
    return render(request, "Menu/Bevande.html")

# ICE CREAM
def Ice_Cream(request):
    return render(request, "Menu/Ice Cream.html")

# CAKE
def Cake(request):
    return render(request, "Menu/Cake.html")

# WINE
def Wine(request):
    return render(request, "Menu/Wine.html")

# WHITE WINE
def Anna_Spinato_Pinot_Grigio(request):
    return render(request, "Menu/Wine/White/Anna Spinato Pinot Grigio.html")

def Finca_Las_Moras_Sauvignon_Blanc(request):
    return render(request, "Menu/Wine/White/Finca Las Moras Sauvignon Blanc.html")

def Villa_Girardi_Pinot_Grigio_Delle_Venezie(request):
    return render(request, "Menu/Wine/White/Villa Girardi Pinot Grigio Delle Venezie.html")

def Wild_Rock_Chardonnay(request):
    return render(request, "Menu/Wine/White/Wild Rock Chardonnay.html")

def Craggy_Range_Chardonnay(request):
    return render(request, "Menu/Wine/White/Craggy Range Chardonnay.html")

def Craggy_Range_Sauvignon_Blanc(request):
    return render(request, "Menu/Wine/White/Craggy Range Sauvignon Blanc.html")


# RED WINE
def Finca_Las_Moras_Malbec(request):
    return render(request, "Menu/Wine/Red/Finca Las Moras Malbec.html")

def Villa_Girardi_Valpolicella_Classico(request):
    return render(request, "Menu/Wine/Red/Villa Girardi Valpolicella Classico.html")

def Beronia_Tempranill(request):
    return render(request, "Menu/Wine/Red/Beronia Tempranill.html")

def Beronia_Crianza_Rioja(request):
    return render(request, "Menu/Wine/Red/Beronia Crianza Rioja.html")

def Wild_Rock_Merlot(request):
    return render(request, "Menu/Wine/Red/Wild Rock Merlot.html")

def Prestige_Chianti_Classico(request):
    return render(request, "Menu/Wine/Red/Prestige Chianti Classico.html")

# BEER
def Birra(request):
    return render(request, "Menu/Birra.html")

# View to render about page
def about(request):
    return render(request, "about.html")

# View to render menu choice page
def menu_choice(request):
    return render(request, "menu_choice.html")

# View to render reservations page
# def reservations(request):
#     return render(request, "reservations.html")

# View to render contact page
def contact(request):
    return render(request, "contact.html")

def feedback(request):
    return render(request, "feedback.html")

# View to render footer
def footer(request):
    return render(request, "footer.html")


# View for admin login
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session.cookie_name = settings.SESSION_COOKIE_NAME
            return redirect('admin_dashboard')  # Redirect to admin dashboard if authentication is successful       
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'Admin/admin_login.html')

# View to register 
def admin_register(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save to DB yet
            user.email = form.cleaned_data['email']
            user.save()  # Now save to DB

            # ✅ Add user to "staff" group
            staff_group, created = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)

            # Authenticate and log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

            messages.success(request, 'Registration successful.')
            return redirect('admin_login')
    else:
        form = AdminRegisterForm()
    return render(request, 'Admin/admin_register.html', {'form': form})


# View to handle user logout
def logout_user(request):
    logout(request)
    messages.success(request, "You Logged Out...")
    return redirect('admin_login')

def error_403 (request, exception):
    # Handle 403 Forbidden errors.
    return render(request, 'Errors/403.html', status=403)

def admin_profile(request):
    if request.user.is_authenticated:
        return render(request, 'Admin/admin_profile.html', {'user':request.user})
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')

def admin_profile_edit(request):
    if request.method == 'POST':
        form = AdminProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('admin_profile')
    else:
        form = AdminProfileForm(instance=request.user)
    return render(request, 'Admin/admin_profile_edit.html', {'form': form})

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'Admin/change_password.html'
    success_url = reverse_lazy('admin_profile')

def admin_dashboard(request):
    if request.user.is_authenticated:
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date', '')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # --- Start with base queryset ---
        normal_reservations = NormalReservationTable.objects.all()

        # --- Filter by search ---
        if search_query:
            normal_reservations = normal_reservations.filter(
                Q(fullname__icontains=search_query) |
                Q(normalreservationorder__dish__dish_name__icontains=search_query)
            ).distinct()

        if date_filter == 'today':
            normal_reservations = normal_reservations.filter(date=date.today())
        elif date_filter == 'this_week':
            normal_reservations = normal_reservations.filter(
                date__range=[date.today(), date.today() + timedelta(days=7)]
            )
        elif date_filter == 'this_month':
            normal_reservations = normal_reservations.filter(
                date__month=date.today().month,
                date__year=date.today().year
            )

        normal_reservations = normal_reservations.annotate(
            lead_time=ExpressionWrapper(F('date') - F('date_created'), output_field=DurationField())
        )

        # Custom Start/End date filter (overrides quick range if used)
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                if end_date:
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                    normal_reservations = normal_reservations.filter(date__range=(start, end))
                else:
                    normal_reservations = normal_reservations.filter(date=start)
            except ValueError:
                pass
        
        # --- Order & paginate ---
        normal_reservations = normal_reservations.order_by('date')
        paginator = Paginator(normal_reservations, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Popular dish count
        popular_dishes = Menu.objects.annotate(
            order_count=Count('normalreservationorder')
        ).filter(order_count__gt=0).order_by('-order_count')

        total_reservations = NormalReservationTable.objects.count()
        pending_reservations = NormalReservationTable.objects.filter(table_status='In progress').count()
        completed_reservations = NormalReservationTable.objects.filter(table_status='Completed').count()

        context = {
            'page_obj': page_obj,
            'popular_dishes': popular_dishes,
            'total_reservations': total_reservations,
            'pending_reservations': pending_reservations,
            'completed_reservations': completed_reservations,
        }

        return render(request, "Admin/admin_dashboard.html", context)
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')

# View to render admin main page
def admin_main(request):
    return render(request, "Admin/admin_main.html")

# View to render dish detail page by the slug
def dish_detail(request, slug):
    dish = get_object_or_404(Menu, slug=slug)
    return render(request, 'Menu/dish_detail.html', {'dish': dish})


@allowed_users(allowed_roles=['Admin', 'Staff'])    
# View to render admin menu page
def admin_menu(request):
    # Check if the user is logged in
    if request.user.is_authenticated:
        menu = Menu.objects.all().order_by('category','sub_category','id')        
        return render(request, "Admin/admin_menu.html", {'menu': menu})
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')

@allowed_users(allowed_roles=['Admin', 'Staff'])
# View to display a specific menu record
def menu_record(request, pk):
    # Check if the user is logged in
    if request.user.is_authenticated:
        menu_record = Menu.objects.get(id=pk)
        return render(request, "Admin/Menu/menu_record.html", {'menu_record': menu_record})
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')
    
@allowed_users(allowed_roles=['Admin'])
# View to add a menu record
def add_menu(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            dish_name = request.POST.get("dish_name")
            category = request.POST.get("category")
            sub_category = request.POST.get("sub_category")
            ingredients = request.POST.get("ingredients")
            price = request.POST.get("price")
            image = request.POST.get("image")
            slug = request.POST.get("slug")

            if dish_name and category and ingredients and price and slug:
                try:
                    Menu.objects.create(
                        dish_name=dish_name,
                        category=category,
                        sub_category=sub_category or "None",
                        ingredients=ingredients,
                        price=price,
                        image=image,
                        slug=slug
                    )
                    messages.success(request, "Record added successfully.")
                    return redirect('admin_menu')
                except Exception as e:
                    messages.error(request, f"An error occurred: {e}")
            else:
                messages.error(request, "Please fill out all required fields.")

        return render(request, "Admin/Menu/add_menu.html")
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')


@allowed_users(allowed_roles=['Admin'])
# View to update a menu record
def update_menu(request, pk):
    # Check if the user is logged in
    if request.user.is_authenticated:
        current_record = Menu.objects.get(id=pk)
        form = MenuForm(request.POST or None,instance=current_record)
        if form.is_valid():
            form.save()
            messages.success(request, "Record Updated Successfully...")
            # return redirect('menu_record', pk=pk)
            return redirect('admin_menu')
        return render(request, "Admin/Menu/update_menu.html", {"form": form})
    else:
        messages.error(request, "You are not logged in!")
        return redirect(request, 'admin_login')
    
@allowed_users(allowed_roles=['Admin'])
# View to delete a menu record
def delete_menu(request, pk):
    # Check if the user is logged in
    if request.user.is_authenticated:
        menu_record = Menu.objects.get(id=pk)
        menu_record.delete()
        messages.success(request, "Record Deleted Successfully...")
        return redirect ('admin_menu')
    else:
        messages.error(request, "You are not logged in!")
        return redirect(request, 'admin_login')

# get_categories, get_subcategories, get_dishesn 
def get_categories(request):
    # categories = Menu.objects.order_by('id').values_list('category', flat=True).distinct()
    categories = Menu.objects.order_by('category').values_list('category', flat=True).distinct()
    
    return JsonResponse({'categories': list(categories)})

def get_subcategories(request, category):
    subcategories = Menu.objects.filter(category=category).values_list('sub_category', flat=True).distinct()

    return JsonResponse({'subcategories': list(subcategories)})

def get_dishes(request, category, subcategory=None):
    if subcategory and subcategory != 'None':
        dishes = Menu.objects.filter(category=category, sub_category=subcategory)
    else:
        dishes = Menu.objects.filter(category=category)
    dishes_list = [{'id': dish.id, 'name': dish.dish_name, 'price': str(dish.price)} for dish in dishes]
    return JsonResponse({'dishes': dishes_list})


@allowed_users(allowed_roles=['Admin', 'Staff'])
def admin_reservation(request):
    if not request.user.is_authenticated:
        messages.error(request, "You are not logged in!")
        return redirect("admin_login")

    search_query = request.GET.get('search', '')
    range_filter = request.GET.get('range', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    reservations = NormalReservationTable.objects.all()

    # Search filter
    if search_query:
        reservations = reservations.filter(
            Q(name__icontains=search_query) |
            Q(time__icontains=search_query) |
            Q(date__icontains=search_query) |
            Q(dish_ordered__order__dish__name__icontains=search_query)
        ).distinct()

    # Quick Range filter
    if range_filter == 'today':
        reservations = reservations.filter(date=today)
    elif range_filter == 'week':
        reservations = reservations.filter(date__range=(week_start, week_end))
    elif range_filter == 'month':
        reservations = reservations.filter(date__year=today.year, date__month=today.month)

    # Custom Start/End date filter (overrides quick range if used)
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                reservations = reservations.filter(date__range=(start, end))
            else:
                reservations = reservations.filter(date=start)
        except ValueError:
            pass

    # Fallback if no results and no specific filters
    if not reservations.exists() and not (search_query or start_date or range_filter):
        reservations = NormalReservationTable.objects.all().order_by('-date')

    reservations = reservations.order_by('-date')

    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "Admin/admin_reservation.html", {
        'page_obj': page_obj,
        'search_query': search_query,
        'range_filter': range_filter,
    })



@allowed_users(allowed_roles=['Admin', 'Staff'])
# View to display a specific reservation record
def reservation_record(request, pk):
    # Check if the user is logged in
    if request.user.is_authenticated:
        reservation_record = NormalReservationTable.objects.get(id=pk)
        return render(request, "Admin/Reservation/reservation_record.html", {'reservation_record': reservation_record})
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')

@allowed_users(allowed_roles=['Admin'])
def add_reservation(request):   
    if request.user.is_authenticated:
        form = NormalReservationForm(request.POST or None)
        
        if request.method == "POST":
            if form.is_valid():
                # Save the basic reservation data
                reservation = form.save(commit=False)
                reservation.total_price = form.cleaned_data['total_price']
                reservation.save()  # Save the reservation instance first
                
                # Retrieve selected dishes and quantities from the hidden input field
                selected_dishes_data = request.POST.get('selected_dishes')
                if selected_dishes_data:
                    try:                        
                        selected_dishes = json.loads(selected_dishes_data)
                        # Loop through selected dishes and quantities and save them
                        for dish_id_str, dish_data in selected_dishes.items():
                            dish_id = int(dish_id_str)
                            quantity = dish_data['quantity']
                            dish = Menu.objects.get(id=dish_id)  # Get the dish instance
                            
                            # Create NormalReservationOrder with the reservation, dish, and quantity
                            NormalReservationOrder.objects.create(
                                reservation=reservation,
                                dish=dish,
                                quantity=quantity
                            )
                    except json.JSONDecodeError as e:
                        print("Error decoding JSON:", e)
                        messages.error(request, "Error decoding the selected dishes data.")
                
                # Print the saved dishes and their quantities
                reservation_dishes = reservation.normalreservationorder_set.all()
                for rd in reservation_dishes:
                    print(f"Dish: {rd.dish.dish_name}, Quantity: {rd.quantity}")

                messages.success(request, "Record added successfully.")
                return redirect('admin_reservation')  # Redirect to the reservation admin page

            else:
                print(form.errors)
                messages.error(request, "Invalid form data.")

        # Render the form with potential errors
        return render(request, 'Admin/Reservation/add_reservation.html', {'form': form})
    
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')

@allowed_users(allowed_roles=['Admin'])
# View to update a specific reservation record
def update_reservation(request, pk):
    if request.user.is_authenticated:
        current_record = NormalReservationTable.objects.get(id=pk)
        form = NormalReservationForm(request.POST or None, instance=current_record)

        selected_dishes_dict = {}

        if request.method == "GET":
            reservation_orders = current_record.normalreservationorder_set.all()
            selected_dishes_dict = {
                str(order.dish.id): {
                    "name": order.dish.dish_name,
                    "price": float(order.dish.price),
                    "quantity": order.quantity
                } for order in reservation_orders
            }
            form = NormalReservationForm(instance=current_record, initial={
                'selected_dishes': json.dumps(selected_dishes_dict)
            })

        elif request.method == "POST":
            if form.is_valid():
                reservation = form.save(commit=False)
                reservation.total_price = form.cleaned_data['total_price']
                reservation.save()

                selected_dishes_data = request.POST.get('selected_dishes')
                if selected_dishes_data:
                    selected_dishes = json.loads(selected_dishes_data)

                    NormalReservationOrder.objects.filter(reservation=reservation).delete()
                    for dish_id_str, dish_data in selected_dishes.items():
                        dish_id = int(dish_id_str)
                        quantity = dish_data.get('quantity', 0)
                        dish = Menu.objects.get(id=dish_id)

                        NormalReservationOrder.objects.create(
                            reservation=reservation,
                            dish=dish,
                            quantity=quantity
                        )

                messages.success(request, "Record Updated Successfully...")
                return redirect('admin_reservation')
            else:
                try:
                    selected_dishes_data = request.POST.get('selected_dishes')
                    if selected_dishes_data:
                        selected_dishes_dict = json.loads(selected_dishes_data)
                except Exception as e:
                    print("Error parsing selected_dishes in POST:", e)

                messages.error(request, "Invalid form data. Please correct the errors.")

        return render(request, "Admin/Reservation/update_reservation.html", {
            "form": form,
            "current_record": current_record,
            "selected_dishes_json": json.dumps(selected_dishes_dict)
        })
    else:
        messages.error(request, "You are not logged in!")
        return redirect('admin_login')



@allowed_users(allowed_roles=['Admin'])
# View to delete a specific reservation record
def delete_reservation(request, pk):
    # Check if the user is logged in
    if request.user.is_authenticated:
        reservation_record = NormalReservationTable.objects.get(id=pk)
        reservation_record.delete()
        messages.success(request, "Record Deleted Successfully...")
        return redirect ('admin_reservation')
    else:
        messages.error(request, "You are not logged in!")
        return redirect(request, 'admin_login')

# SESSION
def session(request):
    if request.user.is_authenticated:
        session = SessionDishHistory.objects.all()
        return render(request, "Admin/session.html", {'session': session})
    else:
        messages.error(request, "You are not logged in!")
        return redirect("admin_login")
    
# UNAVAILABLE DATES AND TIME
@allowed_users(allowed_roles=['Admin', 'Staff'])    
def unavailable_list(request):
    if request.user.is_authenticated:
        unavailables = UnavailableDateTime.objects.all().order_by('date', 'start_time', 'end_time', 'reason')
        return render(request, 'Admin/unavailable_list.html', {'unavailables': unavailables})
    else:
        messages.error(request, "You are not logged in!")
        return redirect("admin_login")

@allowed_users(allowed_roles=['Admin'])
def add_unavailabledatetime(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = UnavailableDateTimeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Unavailable date and time added.')
                return redirect('unavailable_list')
        else:
            form = UnavailableDateTimeForm()
        return render(request, 'Admin/Unavailabledatetime/add_unavailabledatetime.html', {'form': form, 'is_updated': False})
    else:
        messages.error(request, "You are not logged in!")
        return redirect("admin_login")

@allowed_users(allowed_roles=['Admin'])
def update_unavailabledatetime(request, pk):
    if request.user.is_authenticated:
        instance = get_object_or_404(UnavailableDateTime, pk=pk)
        if request.method == 'POST':
            form = UnavailableDateTimeForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, 'Unavailable date and time updated.')
                return redirect('unavailable_list')
        else:
            form = UnavailableDateTimeForm(instance=instance)
        return render(request, 'Admin/Unavailabledatetime/add_unavailabledatetime.html', {'form': form, 'is_updated': True})
    else:
        messages.error(request, "You are not logged in!")
        return redirect("admin_login")

@allowed_users(allowed_roles=['Admin'])
def delete_unavailabledatetime(request, pk):
    if request.user.is_authenticated:

        instance = get_object_or_404(UnavailableDateTime, pk=pk)
        instance.delete()
        messages.success(request, 'Unavailable date and time deleted.')
        return redirect('unavailable_list')
    else:
        messages.error(request, "You are not logged in!")
        return redirect("admin_login")

# FOR NOTIFICATION FOR ADMIN
def check_new_reservations(request):
    last_checked_str = request.GET.get('last_checked')
    
    if not last_checked_str:
        return JsonResponse({'notifications': []})
    
    try:
        last_checked = timezone.datetime.fromisoformat(last_checked_str.replace("Z", "+00:00"))
        if timezone.is_naive(last_checked):
            last_checked = timezone.make_aware(last_checked)
    except ValueError:
        return JsonResponse({'notifications': []})
    
    new_reservations = NormalReservationTable.objects.filter(date_created__gt=last_checked)
    updated_reservations = NormalReservationTable.objects.filter(date_updated__gt=last_checked).exclude(date_created__gt=last_checked)
    
    # ✅ FIXED LINE: table_status instead of status
    canceled_reservations = NormalReservationTable.objects.filter(
        table_status='canceled', date_updated__gt=last_checked
    )

    notifications = []

    for r in new_reservations:
        notifications.append({
            'type': 'new',
            'message': f"New reservation from {r.fullname} on {r.date.strftime('%Y-%m-%d')}"
        })

    for r in updated_reservations:
        notifications.append({
            'type': 'update',
            'message': f"Updated reservation for {r.fullname} on {r.date.strftime('%Y-%m-%d')}"
        })

    for r in canceled_reservations:
        notifications.append({
            'type': 'cancel',
            'message': f"Reservation by {r.fullname} was canceled."
        })

    return JsonResponse({'notifications': notifications})


# redeploy trigger


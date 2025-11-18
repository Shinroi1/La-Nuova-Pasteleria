# INSTALLATION
1. Create a folder where will you put the system.
2. Open it with vs code by going to the VS Code, and then Hold Ctrl + K and O.
3. Then select the folder you created.
4. Click the word Terminal and create new Terminal.
5. Now on the Terminal type: git clone https://github.com/Shinroi1/La-Nuova-Pasteleria.git
6. Let it download first.
7. Now type on the terminal: python -m venv .env
8. Type: .env\scripts\activate
9. cd La-Nuova-Pasteleria
10. Confgure the settings.py for you to run it locally on your VS Code. Do not forget to change the DEBUG, ALLOWED_HOSTS, and use your own database. This system currently use postgresql.

This system is currently for the La Nuova Pasteleria, a small italian restaurant who doesn't have any website. The feature of this are: web system, chatbot (botpress), reservation form with logic-based and a collaborative menu recommender.

# AI ASSISTANT CUSTOMER SUPPORT (BOTPRESS)
- AI Assisstant is multilingual.
- AI Assisstant is only used for FAQs.
- AI Assisstant can only answer related to the restaurant and what has been fed to it.
- AI Assisstant has a feature of storing unanswered questions although the who created it need to manually type an answer.
- The AI Assistant currently uses GPT 4.1 Mini although it cannot store past messages and questions.

# Restaurant Reservation System – Reservation Form Logic

This module handles reservation creation, validation rules, unavailable slot checking, and dish selection logic for a restaurant website built with Django.

---

## 🚀 Features

- Validates reservation times and dates
- Prevents bookings during closed hours
- Enforces minimum advance booking
- Limits maximum party size
- Checks if a time slot is blocked (e.g., private events)
- Saves reservations and selected dishes
- Stores user dish history (only if cookies are accepted)
- Prevents duplicate form submission using session flags

---

## 🧠 Reservation Rules

The reservation system follows these business rules:

| Rule                  | Value |
|-----------------------|-------|
| Opening hour          | 10 AM |
| Closing hour          | 9 PM |
| Max party size        | 12 people |
| Minimum advance time  | 1 day |

These are defined in:

```
OPEN_HOUR = 10
CLOSE_HOUR = 21
MAX_PARTY_SIZE = 12
MIN_ADVANCE_DAY = 1
```

# 🍽️ Collaborative Filtering Menu Recommender — How It Works

This document explains **how our collaborative filtering menu recommender works**, using simple examples, real dish names, and a step-by-step walkthrough of the actual Django code.

The system uses **co-occurrence collaborative filtering**, meaning it recommends dishes that **other similar users** commonly ordered *together* with the user’s chosen dishes.

---

# 📌 1. What Data Do We Use?

We track the user’s selected dishes **only when they give cookie consent** and when they submit a pre-order form.

These orders are stored in: SessionDishHistory

Example of current user’s orders:


---

# 📌 2. How Do We Find Similar Users?

A “similar user” is ANYONE who ordered **at least one** of the same dishes as the current user.

Example dataset:

| User             | Orders |
|------            |--------|
| **Current User** | Lasagna, Carbonara |
| User 2           | Lasagna, Pizza, Garlic Bread |
| User 3           | Carbonara, Pizza, Salad |
| User 4           | Lasagna, Tiramisu |
| User 5           | Carbonara, Pizza, Tiramisu, Garlic Bread |

All these users share at least one dish with the current user → all are **similar users**.

This matches the code:

```python
similar_sessions = (
    SessionDishHistory.objects.filter(dish_id__in=user_dish_ids)
    .exclude(session_key=session_key)
    .values_list('session_key', flat=True)
    .distinct()
)
```

# 3. Get All Other Dishes From Similar Users

We take all dishes similar users ordered, but exclude the dishes the current user already had.

Remaining dishes:

Pizza

Garlic Bread

Tiramisu

Salad

Code:
```
cooc = (
    SessionDishHistory.objects
    .filter(session_key__in=similar_sessions)
    .exclude(dish_id__in=user_dish_ids)
```
# 4. Count Co-Occurrences (Frequency)

This is the core AI logic:

The more users who ordered a dish, the stronger the recommendation.

Frequency counts:

|Dish	        |Count|
|---------------|     |
|Pizza	        |3    |
|Garlic Bread   |2    |
|Tiramisu	    |2    |
|Salad	        |1    |

Django does this with:
```
.annotate(score=Count('session_key', distinct=True))
```

# 5. Rank and Recommend

The highest co-occurrence scores become the final recommendations.

Final ranked output:

1.) Pizza

2.) Garlic Bread

3.) Tiramisu

4.) Salad

Code:
```
.order_by('-score')[:limit]
```

#⭐ Full Flow Summary

1. Get the user’s dish history

2. Find other users who ordered any of the same dishes

3. Collect all dishes those users ordered

4. Remove the dishes the user already had

5. Count the frequency of each remaining dish

6. Recommend the dishes with the highest co-occurrence







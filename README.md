# INSTALLATION
1.


🍽️ Collaborative Filtering Menu Recommender — How It Works

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

Dish	      Count
Pizza	        3
Garlic Bread	2
Tiramisu	    2
Salad	        1

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



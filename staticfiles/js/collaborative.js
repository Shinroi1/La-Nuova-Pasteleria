// Format price with peso style
function formatPrice(value) {
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const defaultHeadingText = "We couldn't find your usual favorites — but no worries! Here's something to spark your appetite:";

// 🔥 Smooth horizontal scroll buttons
function scrollList(direction) {
  const container = document.querySelector(".recommend-scroll");
  if (!container) return;
  const scrollAmount = 300;
  container.scrollBy({ left: direction * scrollAmount, behavior: "smooth" });
}

// 🔥 Show/hide arrow buttons dynamically
function updateScrollButtons() {
  const container = document.querySelector(".recommend-scroll");
  const leftBtn = document.querySelector(".scroll-btn.left");
  const rightBtn = document.querySelector(".scroll-btn.right");
  if (!container || !leftBtn || !rightBtn) return;

  const scrollLeft = container.scrollLeft;
  const maxScroll = container.scrollWidth - container.clientWidth;

  leftBtn.style.display = scrollLeft > 0 ? "block" : "none";
  rightBtn.style.display = scrollLeft < maxScroll - 1 ? "block" : "none";
}

// 🔥 Fade + swap recommendations or bestsellers
function fadeSwapContent(fetchUrl, headingText) {
  const list = document.getElementById("dish-list");
  const heading = document.getElementById("recommendation-heading");

  // Fade out
  list.classList.add("fade-out");

  setTimeout(() => {
    fetch(fetchUrl)
      .then(response => response.json())
      .then(data => {
        const resolvedHeading = data.heading || headingText || defaultHeadingText;
        heading.innerHTML = `<p class="menu-title">${resolvedHeading}</p>`;
        list.innerHTML = '';

        if (!data.dishes || data.dishes.length === 0) {
          const noDataMessage = `
            <div class="col-12 text-center">
              <p class="text-muted">Sorry, we couldn't find any recommended dishes right now. Try browsing our <a href="/menu/">full menu</a>.</p>
            </div>`;
          list.insertAdjacentHTML('beforeend', noDataMessage);
          list.classList.remove("fade-out");
          list.classList.add("fade-in");
          setTimeout(() => list.classList.remove("fade-in"), 500);
          updateScrollButtons();
          return;
        }

        const urlTemplate = list.dataset.urlTemplate;

        data.dishes.forEach(dish => {
          const dishUrl = urlTemplate.replace("__slug__", dish.slug);
          const altText = dish.image_url.includes("default.jpg")
            ? "Image coming soon"
            : dish.name;

          const dishCard = `
            <div class="card h-100 shadow-sm">
              <a href="${dishUrl}" class="text-decoration-none text-dark">
                <img src="${dish.image_url}" class="card-img-top" alt="${altText}" style="max-height: 200px; object-fit: cover;">
                <div class="card-body text-center">
                  <h5 class="card-title">${dish.name} - ${dish.category}</h5>
                  <h6>&#8369; ${formatPrice(dish.price)}</h6>
                </div>
              </a>
            </div>`;
          list.insertAdjacentHTML('beforeend', dishCard);
        });

        list.classList.remove("fade-out");
        list.classList.add("fade-in");
        setTimeout(() => list.classList.remove("fade-in"), 500);

        updateScrollButtons(); // 🔥 check arrows after new content
      })
      .catch(error => {
        console.error("Error fetching dishes:", error);
        list.innerHTML = `<p class="text-danger text-center w-100">Failed to load dishes.</p>`;
        list.classList.remove("fade-out");
        updateScrollButtons();
      });
  }, 500);
}

// === Past Orders + Recommendations cycling ===
let userPastOrders = [];
let currentOrderIndex = 0;

// Fetch user's past orders once
function fetchUserPastOrders() {
  return fetch("/get_user_past_orders/")
    .then(res => res.json())
    .then(data => {
      userPastOrders = data.dish_ids || [];
      currentOrderIndex = 0;
    });
}

// Surpise me button logic
function getAlternativeRecommendations() {
  const btn = document.getElementById("recommend-more");
  const personalized = btn.dataset.personalized === "true";
  const cookiesAccepted = btn.dataset.cookies === "true";

  if (personalized && cookiesAccepted && userPastOrders.length > 0) {
    // Use user's past orders
    const dishId = userPastOrders[currentOrderIndex];
    fadeSwapContent(`/get_recommendations_for_dish/${dishId}/`, `Since you ordered...`);
    currentOrderIndex = (currentOrderIndex + 1) % userPastOrders.length;
  } else {
    // Random / general recommendations
    fadeSwapContent("/recommend_alternatives/", "Finding something delicious for you...");
  }
}

// 🔥 Bestsellers button
function getBestsellers() {
  fadeSwapContent("/get_bestsellers/", "Check out our bestsellers!");
}


// Attach scroll listener for live arrow toggle & button label change
document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".recommend-scroll");
  if (container) {
    container.addEventListener("scroll", updateScrollButtons);
    window.addEventListener("resize", updateScrollButtons);
    updateScrollButtons(); // run once
  }

  const btn = document.getElementById("recommend-more");
  const personalized = btn.dataset.personalized === "true";
  const cookiesAccepted = btn.dataset.cookies === "true";

  if (personalized && cookiesAccepted) {
    fetchUserPastOrders();

    // 🔹 Change button text if user has past orders
    btn.innerText = "Recommend me with my orders";
  } else {
    btn.innerText = "Surprise Me!";
  }
});

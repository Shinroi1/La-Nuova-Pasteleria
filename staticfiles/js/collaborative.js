function formatPrice(value) {
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const defaultHeadingText = "We couldn't find your usual favorites — but no worries! Here's something to spark your appetite:";

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
          return;
        }

        const urlTemplate = list.dataset.urlTemplate;
        const placeholderImage = "/static/images/default.jpg";

        data.dishes.forEach(dish => {
          const dishUrl = urlTemplate.replace("__slug__", dish.slug);
          const isPlaceholder = dish.image_url.includes("default.jpg");
          const altText = isPlaceholder ? "Image coming soon" : dish.name;

          const dishCard = `
            <div class="col-md-4 mb-4">
              <a href="${dishUrl}" class="text-decoration-none text-dark">
                <div class="card h-100 shadow-sm">
                  <img src="${dish.image_url}" class="card-img-top" alt="${altText}" style="max-height: 250px; object-fit: cover;">
                  <div class="card-body text-center">
                    <h5 class="card-title">${dish.name} - ${dish.category}</h5>
                    <h6>&#8369; ${formatPrice(dish.price)}</h6>
                  </div>
                </div>
              </a>
            </div>`;
          list.insertAdjacentHTML('beforeend', dishCard);
        });

        list.classList.remove("fade-out");
        list.classList.add("fade-in");
        setTimeout(() => list.classList.remove("fade-in"), 500);
      });
  }, 500);
}


function getAlternativeRecommendations() {
  fadeSwapContent("/recommend_alternatives/", "Finding recommendations for you...");
}

function showBestsellers() {
  fadeSwapContent("/get_bestsellers/", "Check out our bestsellers!");
}

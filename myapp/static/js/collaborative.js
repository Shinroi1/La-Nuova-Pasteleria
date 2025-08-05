function formatPrice(value) {
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return num.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}


function fadeSwapContent(fetchUrl, headingText) {
  const list = document.getElementById("dish-list");
  const heading = document.getElementById("recommendation-heading");

  // Fade out
  list.classList.add("fade-out");

  setTimeout(() => {
    // Fetch new data after fade-out
    fetch(fetchUrl)
      .then(response => response.json())
      .then(data => {
        heading.innerHTML = `<p class="menu-title">${headingText}</p>`;
        list.innerHTML = ''; 

        // 
        if (!data.dishes || data.dishes.length === 0) {
          const noDataMessage = `
            <div class="col-12 text-center">
              <p class="text-muted">Sorry, we couldn't find any recommended dishes right now. Try browsing our <a href="/menu/">full menu</a>.</p>
            </div>`;
          list.insertAdjacentHTML('beforeend', noDataMessage);
          
          // Fade in the message
          list.classList.remove("fade-out");
          list.classList.add("fade-in");
          setTimeout(() => list.classList.remove("fade-in"), 500);
          return; // Skip rendering cards
        }


        const urlTemplate = list.dataset.urlTemplate;

        data.dishes.forEach(dish => {
          const dishUrl = urlTemplate.replace("__slug__", dish.slug);
          const dishCard = `
            <div class="col-md-4 mb-4">
              <a href="${dishUrl}" class="text-decoration-none text-dark">
                <div class="card h-100 shadow-sm">
                  <img src="${dish.image_url}" class="card-img-top" alt="${dish.name}" style="max-height: 250px; object-fit: cover;">
                  <div class="card-body text-center">
                    <h5 class="card-title">${dish.name} - ${dish.category}</h5>
                    <h6>&#8369; ${formatPrice(dish.price)}</h6>
                  </div>
                </div>
              </a>
            </div>`;
          list.insertAdjacentHTML('beforeend', dishCard);
        });


        // Fade in
        list.classList.remove("fade-out");
        list.classList.add("fade-in");

        // Optional: remove the fade-in class after animation
        setTimeout(() => list.classList.remove("fade-in"), 500);
      });
  }, 500); // Wait for fade-out to finish
}

function getAlternativeRecommendations() {
  fadeSwapContent("/recommend_alternatives/", "Other customers also ordered these:");
}

function showBestsellers() {
  fadeSwapContent("/get_bestsellers/", "Check out our bestsellers!");
}
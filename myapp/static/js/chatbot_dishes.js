if (window.jQuery) {
  console.log("jQuery is loaded");
} else {
  console.log("jQuery is not loaded");
}

// Simple search filter
document.getElementById('dishSearch').addEventListener('input', function() {
  const filter = this.value.toLowerCase();
  const dishItems = document.querySelectorAll('#dishes-chatbot .dish-item');
  dishItems.forEach(function(item) {
    const dishName = item.querySelector('.dish-name').textContent.toLowerCase();
    item.style.display = dishName.indexOf(filter) > -1 ? '' : 'none';
  });
});


document.addEventListener("DOMContentLoaded", function() {
let selectedDishes = {}; // Global object to retain selected dishes

// When the chatbot modal opens, load all dishes directly
$('#dishModalChatbot').on('show.bs.modal', function (event) {
    // Optionally hide any unused sections if they exist
    $('#categories-chatbot, #subcategories-chatbot').hide();
    loadAllDishes();
});

// Function to load all dishes (bypassing categories and subcategories)
function loadAllDishes() {
    $.ajax({
        url: '/get_all_dishes/',  // Backend endpoint that returns all dishes
        type: 'GET',
        success: function(response) {
            let dishesHtml = '';
            response.dishes.forEach(function(dish) {
                // Retain previously selected quantity if available
                const quantity = selectedDishes[dish.id] ? selectedDishes[dish.id].quantity : 0;
                dishesHtml += `
                <div class="dish-item mb-2">
                    <span class="dish-name">${dish.name}</span> - $${dish.price} 
                    <input type="number" class="dish-quantity" data-dish-id="${dish.id}" min="0" value="${quantity}" style="width: 60px;">
                </div>`;
            });
            $('#dishes-chatbot').html(dishesHtml).show();
        },
        error: function(xhr, status, error) {
            console.error("Error loading dishes:", error);
        }
    });
}

// Save selected dishes and quantities when clicking the save button
$('#saveSelection').click(function() {
  // Update global selectedDishes object with current selections
  $('.dish-quantity').each(function() {
    const dishId = $(this).data('dish-id');
    const quantity = parseInt($(this).val(), 10); // Convert to an integer
    const dishName = $(this).closest('.dish-item').find('.dish-name').text().trim();

    if (quantity > 0) {
      selectedDishes[dishId] = { 
        quantity: quantity,
        name: dishName 
      };
    } else {
      delete selectedDishes[dishId];
    }
  });

  // Update the modal display with selected dishes
  let modalSelectedDishesHtml = '';
  for (const dishId in selectedDishes) {
    const { quantity, name } = selectedDishes[dishId];
    modalSelectedDishesHtml += `<div>${name} - Quantity: ${quantity}</div>`;
  }
  $('#selectedDishesListModal').html(modalSelectedDishesHtml);

  // (Optional) If you need to pass this data to a form field, update it here.
  $('#selectedDishesInput').val(JSON.stringify(selectedDishes));    
});
});

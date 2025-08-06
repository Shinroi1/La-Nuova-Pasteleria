let selectedDishes = {};

// ✅ First define this function early to avoid ReferenceError
function updateSelectedDishesDisplay() {
    let total = 0;
    let modalHtml = '';
    let formHtml = '';

    for (const dishId in selectedDishes) {
        const { name, quantity, price } = selectedDishes[dishId];
        total += quantity * price;
        modalHtml += `
            <div class="d-flex justify-content-between align-items-center mb-2 selected-dish-entry" data-dish-id="${dishId}">
                <span>${name} - Quantity: ${quantity}</span> 
                <button type="button" class="btn btn-sm btn-danger remove-dish-btn" data-dish-id="${dishId}">Remove</button>
            </div>
        `;
        formHtml += `<div>${name} - Quantity: ${quantity}</div>`;
    }

    $('#total-price').val(total.toFixed(2));
    $('#selectedDishesListModal').html(modalHtml).attr('readonly', true);
    $('#selectedDishesListForm').html(formHtml).attr('readonly', true);
    $('#selectedDishesInput').val(JSON.stringify(selectedDishes));

    if ($('#dishModalExclusive').hasClass('show')) {
        $('#selectedDishesInputExclusive').val(JSON.stringify(selectedDishes));
    }
}

// ✅ Safely initialize selectedDishes from hidden input
const initialSelected = document.getElementById('selectedDishesInput')?.value;
if (initialSelected) {
    try {
        selectedDishes = JSON.parse(initialSelected);
        document.addEventListener("DOMContentLoaded", updateSelectedDishesDisplay);
    } catch (e) {
        console.error("Invalid JSON in selectedDishesInput", e);
    }
}

// Debug: check jQuery
if (window.jQuery) {
    console.log("jQuery is loaded");
} else {
    console.log("jQuery is not loaded");
}

// ✅ Reload on browser back/forward
if (performance.navigation.type === 2 || (window.performance.getEntriesByType && window.performance.getEntriesByType("navigation")[0]?.type === "back_forward")) {
    location.reload(true);
}

// ✅ CSRF setup
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!/^GET|HEAD|OPTIONS|TRACE$/i.test(settings.type) && token) {
            xhr.setRequestHeader("X-CSRFToken", token);
        }
    }
});

document.addEventListener("DOMContentLoaded", function() {

    // Dish removal
    $(document).on('click', '.remove-dish-btn', function () {
        const dishId = $(this).data('dish-id');
        delete selectedDishes[dishId];

        const quantityDisplay = $(`.quantity-control[data-dish-id="${dishId}"] .quantity-display`);
        if (quantityDisplay.length > 0) {
            quantityDisplay.text("0");
        }

        updateSelectedDishesDisplay();
    });

    // Modal open handlers
    $('#dishModalNormal').on('show.bs.modal', function () {
        loadCategories('normal');
    });

    $('#dishModalExclusive').on('show.bs.modal', function () {
        loadCategories('exclusive');
    });

    function loadCategories(modalType) {
        $.ajax({
            url: '/get_categories/',
            type: 'GET',
            success: function(response) {
                let categoriesHtml = '';
                response.categories.forEach(function(category) {
                    categoriesHtml += `<button type="button" class="category-btn btn btn-outline-primary" data-category="${category}">${category}</button>`;
                });

                if (modalType === 'normal') {
                    $('#categories-normal').html(categoriesHtml);
                } else {
                    $('#categories-exclusive').html(categoriesHtml);
                }

                $('.category-btn').off('click').on('click', function() {
                    const category = $(this).data('category');
                    loadSubcategories(category, modalType);
                });
            }
        });
    }

    function loadSubcategories(category, modalType) {
        if (modalType === 'normal') {
            $('#subcategories').empty().hide();
            $('#dishes').empty().hide();
        } else {
            $('#subcategories-exclusive').empty().hide();
            $('#dishes-exclusive').empty().hide();
        }

        $.ajax({
            url: `/get_subcategories/${category}/`,
            type: 'GET',
            success: function(response) {
                let subcategoriesHtml = '';
                const validSubcategories = response.subcategories.filter(
                    s => s !== null && s !== '' && String(s).toLowerCase() !== 'none'
                );

                if (validSubcategories.length > 0) {
                    validSubcategories.forEach(function(subcategory) {
                        subcategoriesHtml += `<button type="button" class="subcategory-btn btn btn-secondary" data-subcategory="${subcategory}">${subcategory}</button>`;
                    });

                    if (modalType === 'normal') {
                        $('#subcategories').html(subcategoriesHtml).show();
                    } else {
                        $('#subcategories-exclusive').html(subcategoriesHtml).show();
                    }

                    $('.subcategory-btn').off('click').on('click', function() {
                        const subcategory = $(this).data('subcategory');
                        loadDishes(category, subcategory, modalType);
                    });
                } else {
                    loadDishes(category, null, modalType);
                }
            }
        });
    }

    function loadDishes(category, subcategory, modalType) {
        let url = `/get_dishes/${category}/`;
        if (subcategory) url += `${subcategory}/`;

        if (modalType === 'normal') {
            $('#dishes').empty().hide();
        } else {
            $('#dishes-exclusive').empty().hide();
        }

        $.ajax({
            url: url,
            type: 'GET',
            success: function(response) {
                let dishesHtml = '';
                response.dishes.forEach(function(dish) {
                    const existing = selectedDishes[dish.id];
                    const quantity = existing ? existing.quantity : 0;

                    dishesHtml += `
                        <div class="dish-item d-flex align-items-center justify-content-between mb-2" data-dish-id="${dish.id}">
                            <div>
                                <strong class="dish-name">${dish.name}</strong><br>
                                <span>₱${dish.price}</span>
                            </div>
                            <div class="quantity-control" data-dish-id="${dish.id}">
                                <button type="button" class="btn btn-sm btn-outline-secondary minus-btn">−</button>
                                <span class="mx-2 quantity-display">${quantity}</span>
                                <button type="button" class="btn btn-sm btn-outline-secondary plus-btn">+</button>
                            </div>
                        </div>
                    `;
                });

                if (modalType === 'normal') {
                    $('#dishes').html(dishesHtml).show();
                } else {
                    $('#dishes-exclusive').html(dishesHtml).show();
                }
            }
        });

        updateSelectedDishesDisplay();
    }

    // Quantity buttons
    $(document).on('click', '.plus-btn', function () {
        const parent = $(this).closest('.quantity-control');
        const dishId = parent.data('dish-id');
        const quantityDisplay = parent.find('.quantity-display');
        let quantity = parseInt(quantityDisplay.text(), 10) || 0;
        quantity++;
        quantityDisplay.text(quantity);
        updateDishSelection(dishId, quantity);
    });

    $(document).on('click', '.minus-btn', function () {
        const parent = $(this).closest('.quantity-control');
        const dishId = parent.data('dish-id');
        const quantityDisplay = parent.find('.quantity-display');
        let quantity = parseInt(quantityDisplay.text(), 10) || 0;
        if (quantity > 0) quantity--;
        quantityDisplay.text(quantity);
        updateDishSelection(dishId, quantity);
    });

    // Update dish data in selection
    function updateDishSelection(dishId, quantity) {
        const dishItem = $(`[data-dish-id="${dishId}"]`).closest('.dish-item');
        const dishName = dishItem.find('.dish-name').text().trim();
        const priceMatch = dishItem.html().match(/₱([0-9]+(?:\.[0-9]{1,2})?)/);
        const price = priceMatch ? parseFloat(priceMatch[1]) : 0;

        if (quantity > 0) {
            selectedDishes[dishId] = { quantity, name: dishName, price };
        } else {
            delete selectedDishes[dishId];
        }

        updateSelectedDishesDisplay();
    }

    // Save button click
    $('#saveSelection').off('click').on('click', function() {
        updateSelectedDishesDisplay();
    });
});

document.addEventListener("DOMContentLoaded", function() {
    let selectedDishes = {};

    // Only initialize if on the admin update page
    const updateForm = document.querySelector('form[action*="update_reservation"]');
    const hiddenDishesField = document.getElementById('selectedDishesInput');

    if (updateForm && hiddenDishesField) {
        const existingDishes = hiddenDishesField.value;
        if (existingDishes) {
            try {
                selectedDishes = JSON.parse(existingDishes);
                updateSelectedDishesDisplay();
            } catch (e) {
                console.error("Error parsing existing dish data:", e);
            }
        }
    }

    $('#dishModalNormal').on('show.bs.modal', function () {
        loadCategories('normal');
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
                $('#categories-normal').html(categoriesHtml);

                $('.category-btn').off('click').on('click', function() {
                    const category = $(this).data('category');
                    loadSubcategories(category, modalType);
                });
            }
        });
    }

    function loadSubcategories(category, modalType) {
        $('#subcategories').empty().hide();
        $('#dishes').empty().hide();

        $.ajax({
            url: `/get_subcategories/${category}/`,
            type: 'GET',
            success: function(response) {
                const validSubcategories = response.subcategories.filter(s => s);
                if (validSubcategories.length > 0) {
                    let subcategoriesHtml = '';
                    validSubcategories.forEach(function(subcategory) {
                        subcategoriesHtml += `<button type="button" class="subcategory-btn btn btn-secondary" data-subcategory="${subcategory}">${subcategory}</button>`;
                    });
                    $('#subcategories').html(subcategoriesHtml).show();

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

        $('#dishes').empty().hide();

        $.ajax({
            url: url,
            type: 'GET',
            success: function(response) {
                let dishesHtml = '';
                response.dishes.forEach(function(dish) {
                    const quantity = selectedDishes[dish.id] ? selectedDishes[dish.id].quantity : 0;
                    dishesHtml += `
                        <div class="dish-item d-flex align-items-center justify-content-between mb-2">
                            <div>
                                <strong class="dish-name">${dish.name}</strong><br>
                                <span>$${dish.price}</span>
                            </div>
                            <div class="quantity-control" data-dish-id="${dish.id}">
                                <button type="button" class="btn btn-sm btn-outline-secondary minus-btn">−</button>
                                <span class="mx-2 quantity-display">${quantity}</span>
                                <button type="button" class="btn btn-sm btn-outline-secondary plus-btn">+</button>
                            </div>
                        </div>
                    `;
                });
                $('#dishes').html(dishesHtml).show();
            }
        });
    }

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

    function updateDishSelection(dishId, quantity) {
        const dishItem = $(`[data-dish-id="${dishId}"]`).closest('.dish-item');
        const dishName = dishItem.find('.dish-name').text().trim();
        const priceMatch = dishItem.html().match(/\$([0-9]+(?:\.[0-9]{1,2})?)/);
        const price = priceMatch ? parseFloat(priceMatch[1]) : 0;

        if (quantity > 0) {
            selectedDishes[dishId] = { quantity, name: dishName, price };
        } else {
            delete selectedDishes[dishId];
        }

        updateSelectedDishesDisplay();
    }

    $('#saveSelection').on('click', function () {
        updateSelectedDishesDisplay();
    });

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
        $('#selectedDishesListModal').html(modalHtml);
        $('#selectedDishesListForm').html(formHtml);
        $('#selectedDishesInput').val(JSON.stringify(selectedDishes));
    }
});

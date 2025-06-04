document.addEventListener("DOMContentLoaded", () => {
    const addToCartButtons = document.querySelectorAll(".btn.btn-custom");

    addToCartButtons.forEach((button, index) => {
        button.addEventListener("click", () => {
            const itemContainer = button.closest(".item-container");
            const productName = itemContainer.querySelector("h5 strong").textContent;
            const quantityInput = itemContainer.querySelector(".quantity-input");
            const quantity = parseInt(quantityInput.value, 10) || 0;

            if (quantity <= 0) {
                alert("Please enter a valid quantity.");
                return;
            }

            const data = {
                name: productName,
                quantity: quantity
            };

            fetch("/add_to_cart", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                })
                .then((response) => response.json())
                .then((result) => {
                    if (result.success) {
                        alert("Added to cart successfully!");
                    } else {
                        alert("Error adding to cart: " + result.error);
                    }
                })
                .catch((error) => console.error("Error:", error));
        });
    });









    const removeButtons = document.querySelectorAll(".btn.btn-custom");

    removeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const itemContainer = button.closest(".cart-item-container");
            const productName = itemContainer.querySelector("p strong").textContent;

            fetch("/remove_from_cart", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        name: productName
                    }),
                })
                .then((response) => response.json())
                .then((result) => {
                    if (result.success) {
                        alert("Item removed from cart!");
                        itemContainer.remove();
                        updateOrderSummary();
                    } else {
                        alert("Error removing item: " + result.error);
                    }
                })
                .catch((error) => console.error("Error:", error));
        });
    });

    function updateOrderSummary() {
        const allItems = document.querySelectorAll(".cart-item-container");
        let total = 0;

        allItems.forEach((item) => {
            const quantity = parseInt(item.querySelector("p:nth-of-type(2)").textContent.split(": ")[1], 10);
            const price = parseFloat(item.querySelector("p:nth-of-type(3)").textContent.split(": $")[1]);
            total += quantity * price;
        });

        document.querySelector(".order-summary-row p:last-child").textContent = `$${total.toFixed(2)}`;
    }




    function updateCartCount() {
        fetch("/cart_count")
            .then(response => response.json())
            .then(data => {
                const cartCountElement = document.querySelector(".cart-items-number");
                if (cartCountElement) {
                    cartCountElement.textContent = data.cart_count;
                }
            })
            .catch(error => console.error("Error fetching cart count:", error));
    }


    function addToCart(productId, buttonElement) {
        const itemContainer = buttonElement.closest(".item-container");
        const quantityInput = itemContainer.querySelector(".quantity-input");
        const quantity = parseInt(quantityInput.value, 10) || 0;

        if (quantity <= 0) {
            alert("Please enter a valid quantity.");
            return;
        }
        fetch('/add_to_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: 123,
                quantity: 1
            })
        }).then(response => {
            if (response.ok) {
                console.log("Item added successfully");
            } else {
                console.error("Failed to add item");
            }
        });


    }

    function removeFromCart(productId) {
        fetch("/remove_from_cart", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    productId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateCartCount();
                    location.reload();
                } else {
                    alert(data.message || "Error removing from cart.");
                }
            })
            .catch(error => console.error("Error removing from cart:", error));
    }




});

document.addEventListener("DOMContentLoaded", () => {
    const deliveryOptions = document.querySelectorAll('input[name="delivery-option"]');
    const shippingFeeElement = document.getElementById("shipping-fee");
    const orderTotalElement = document.getElementById("order-total");

    deliveryOptions.forEach(option => {
        option.addEventListener("change", () => {
            const selectedFee = parseFloat(option.value);
            const itemsTotal = parseFloat(orderTotalElement.dataset.itemsTotal);

            shippingFeeElement.textContent = `$${selectedFee.toFixed(2)}`;
            const totalWithShipping = itemsTotal + selectedFee;
            orderTotalElement.textContent = `$${totalWithShipping.toFixed(2)}`;

            document.getElementById("selected-shipping-fee").value = selectedFee;
        });
    });
});


document.addEventListener('DOMContentLoaded', () => {
    const shippingOptions = document.querySelectorAll('input[name="delivery_option"]');
    const shippingFeeElement = document.getElementById('shipping-fee');
    const orderTotalElement = document.getElementById('order-total');
    const itemsTotal = parseFloat(orderTotalElement.getAttribute('data-items-total'));
    const hiddenShippingFee = document.getElementById("hidden-shipping-fee");


    shippingOptions.forEach(option => {
        option.addEventListener('change', () => {
            const selectedFee = parseFloat(option.value);
            const newTotal = itemsTotal + selectedFee;
            shippingFeeElement.textContent = `$${selectedFee.toFixed(2)}`;
            orderTotalElement.textContent = `$${newTotal.toFixed(2)}`;


            console.log(`Shipping fee selected: ${selectedFee}`);
            document.getElementById('selected-shipping-fee').value = selectedFee;
            fetch('/update_shipping_fee', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        shipping_fee: selectedFee
                    })
                })
                .then(response => response.json())
                .then(data => console.log('Shipping fee updated:', data))
                .catch(error => console.error('Error updating shipping fee:', error));

            const placeOrderButton = document.querySelector('.place-order');
            document.querySelectorAll('input[name="delivery_option"]').forEach(radio => {
                radio.addEventListener('change', () => {
                    placeOrderButton.disabled = false;
                });
            });

        });
    });


    const placeOrderButton = document.querySelector('.place-order');
    document.querySelectorAll('input[name="delivery_option"]').forEach(radio => {
        radio.addEventListener('change', () => {
            placeOrderButton.disabled = false;
        });
    });
});

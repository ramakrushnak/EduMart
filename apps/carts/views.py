from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Cart, CartItem

# Local imports to avoid circular imports at module load
from apps.orders.models import Order, OrderItem
from apps.transactions.models import Transaction
import uuid


def cart_page(request):
    """Render the user's cart summary page."""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to view your cart.')
        return redirect('product_list')

    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})


def clear_cart(request):
    """Remove all items from the user's cart."""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to view your cart.')
        return redirect('product_list')

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.all().delete()
    messages.success(request, 'Your cart has been cleared.')
    return redirect('cart_page')


def update_cart_item(request):
    """Update quantity for a cart item (POST).

    Expects `item_id` and `quantity` in POST data.
    If quantity <= 0 the item is removed.
    """
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to update your cart.')
        return redirect('product_list')

    if request.method != 'POST':
        return redirect('cart_page')

    item_id = request.POST.get('item_id')
    qty = request.POST.get('quantity')

    try:
        quantity = int(qty)
    except (TypeError, ValueError):
        messages.error(request, 'Invalid quantity.')
        return redirect('cart_page')

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if quantity <= 0:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated.')

    return redirect('cart_page')


def remove_cart_item(request):
    """Remove a single cart item (POST)."""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to update your cart.')
        return redirect('product_list')

    if request.method != 'POST':
        return redirect('cart_page')

    item_id = request.POST.get('item_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart_page')


def checkout(request):
    """Render checkout page and handle Cash-On-Delivery order placement."""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to checkout.')
        return redirect('login_page')

    cart, _ = Cart.objects.get_or_create(user=request.user)

    if request.method == 'POST' and request.POST.get('action') == 'place_order':
        shipping_address = request.POST.get('shipping_address', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not shipping_address:
            messages.error(request, 'Shipping address is required to place an order.')
            return render(request, 'checkout.html', {'cart': cart})

        # Create order
        order = Order.objects.create(
            user=request.user,
            school=getattr(request.user, 'school', None),
            shipping_address=shipping_address,
            notes=notes,
            total_amount=0
        )

        # Copy cart items to order
        for cart_item in cart.items.select_related('product').all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                discount_percentage=cart_item.product.discount_percentage,
                tax_percentage=cart_item.product.tax_percentage,
            )

        # Calculate totals
        order.calculate_total()

        # Create a transaction record representing Cash On Delivery
        txn = Transaction.objects.create(
            order=order,
            user=request.user,
            amount=order.total_amount,
            status='COMPLETED',
            payment_method='MOCK',
            transaction_id=str(uuid.uuid4()),
        )

        # Mark order as confirmed for COD
        order.update_status('CONFIRMED')

        # Clear the cart
        cart.items.all().delete()

        messages.success(request, f'Order placed successfully (ID: {order.id}).')
        return redirect('order_confirmation', order_id=order.id)

    # GET
    return render(request, 'checkout.html', {'cart': cart})


def order_confirmation(request, order_id):
    """Show a simple order confirmation page."""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to view your order.')
        return redirect('login_page')

    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})

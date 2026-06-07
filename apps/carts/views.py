from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Cart


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

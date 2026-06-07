from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Product
from apps.carts.models import Cart, CartItem, CartCacheService


def product_list(request):
    """Render the public product listing page."""
    products = Product.objects.filter(is_active=True).select_related('category')
    return render(request, 'product_list.html', {
        'products': products,
    })


@require_POST
def add_to_cart(request):
    """Add a product to the logged-in user's cart."""
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to add items to your cart.')
        return redirect('product_list')

    product_id = request.POST.get('product_id')
    quantity_value = request.POST.get('quantity', '1')
    try:
        quantity = max(1, int(quantity_value))
    except (TypeError, ValueError):
        quantity = 1

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        item.quantity += quantity
        item.save()

    CartCacheService.delete_cart(str(request.user.id))
    messages.success(request, f'Added "{product.product_name}" to your cart.')
    return redirect('product_list')

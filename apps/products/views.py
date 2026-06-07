from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from .models import Product, ProductCategory
from apps.carts.models import Cart, CartItem, CartCacheService


def home_page(request):
    """Render the homepage with category quick-links."""
    categories = ProductCategory.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('display_order', 'name')
    return render(request, 'home.html', {
        'categories': categories,
    })


def product_list(request):
    """Render the public product listing page."""
    categories = ProductCategory.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('display_order', 'name')
    category_id = request.GET.get('category_id')
    products = Product.objects.filter(is_active=True).select_related('category')
    selected_category = None

    if category_id:
        selected_category = get_object_or_404(ProductCategory, id=category_id, is_active=True)
        products = products.filter(category=selected_category)

    return render(request, 'product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
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

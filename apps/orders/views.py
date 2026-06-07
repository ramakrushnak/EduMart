from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Order


@login_required
def orders_list(request):
    """Show a simple list of the user's orders."""
    from django.core.paginator import Paginator

    orders_qs = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Attach expected_delivery (7 days) to each order instance for template
    from datetime import timedelta
    for order in page_obj.object_list:
        order.expected_delivery = None
        if order.created_at:
            order.expected_delivery = order.created_at + timedelta(days=7)

    return render(request, 'orders_list.html', {'page_obj': page_obj})


@login_required
def order_detail(request, order_id):
    """Show detailed view for a single order including items and expected delivery."""
    from django.shortcuts import get_object_or_404
    from datetime import timedelta
    from django.utils import timezone

    order = get_object_or_404(Order, id=order_id, user=request.user)
    expected_delivery = None
    if order.created_at:
        expected_delivery = (order.created_at + timedelta(days=7))

    # Prepare status progression
    status_flow = ['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED']
    current_index = 0
    try:
        current_index = status_flow.index(order.status)
    except ValueError:
        current_index = 0

    steps = []
    for idx, s in enumerate(status_flow):
        steps.append({'status': s, 'active': idx <= current_index})

    # Transaction reference if available
    tracking = None
    try:
        txn = order.transaction
        tracking = txn.reference_number or txn.transaction_id
    except Exception:
        tracking = None

    return render(request, 'order_detail.html', {
        'order': order,
        'expected_delivery': expected_delivery,
        'steps': steps,
        'tracking': tracking,
    })

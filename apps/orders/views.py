from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Order


@login_required
def orders_list(request):
    """Show a simple list of the user's orders."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders_list.html', {'orders': orders})

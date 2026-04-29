from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.forms import ShopItemForm
from core.models import ShopItem, ShopPurchase
from core.utils import InsufficientFunds, process_transaction


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
def shop_view(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    sort = request.GET.get('sort', 'featured').strip()
    item_form = ShopItemForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if item_form.is_valid():
            item = item_form.save()
            messages.success(request, f'נוסף פריט חדש לחנות: {item.name}.')
            return redirect('shop')
        messages.error(request, 'לא הצלחנו לשמור את הפריט. בדקו את השדות המסומנים.')

    items = ShopItem.objects.filter(is_active=True)
    if query:
        items = items.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__icontains=query)
            | Q(redemption_code__icontains=query)
        )
    if category:
        items = items.filter(category=category)

    items = items.annotate(purchase_count=Count('purchases', distinct=True))

    if sort == 'price_asc':
        items = items.order_by('price_coins', 'sort_order', 'name')
    elif sort == 'price_desc':
        items = items.order_by('-price_coins', 'sort_order', 'name')
    elif sort == 'popular':
        items = items.order_by('-purchase_count', 'sort_order', 'name')
    else:
        items = items.order_by('-is_featured', 'sort_order', 'price_coins', 'name')

    featured_items = ShopItem.objects.filter(is_active=True, is_featured=True).order_by('sort_order', 'price_coins', 'name')[:3]
    categories = list(
        ShopItem.objects.filter(is_active=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )
    recent_purchases = (
        request.user.shop_purchases.select_related('item')
        .order_by('-created_at')[:8]
    )

    context = {
        'items': items,
        'featured_items': featured_items,
        'categories': categories,
        'selected_category': category,
        'current_sort': sort,
        'query': query,
        'profile': request.user.profile,
        'recent_purchases': recent_purchases,
        'item_form': item_form,
        'show_item_modal': request.method == 'POST' and item_form.errors,
    }
    return render(request, 'core/shop.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='home')
@require_POST
def purchase_shop_item(request, item_id):

    item = get_object_or_404(ShopItem, pk=item_id, is_active=True)

    try:
        with transaction.atomic():
            locked_item = ShopItem.objects.select_for_update().get(pk=item.pk)
            if locked_item.stock_quantity == 0:
                raise ValueError('המוצר אזל מהמלאי.')

            if locked_item.stock_quantity is not None:
                locked_item.stock_quantity -= 1
                locked_item.save(update_fields=['stock_quantity'])

            process_transaction(
                request.user,
                -locked_item.price_coins,
                tx_type='purchase',
                description=f'רכישת {locked_item.name} בחנות המטבעות',
                notify=True,
                bonus_increases_lifetime=False,
            )

            purchase = ShopPurchase.objects.create(
                user=request.user,
                item=locked_item,
                item_name=locked_item.name,
                category=locked_item.category,
                coins_spent=locked_item.price_coins,
                delivery_code=locked_item.redemption_code,
                delivery_instructions=locked_item.redemption_instructions,
            )
    except InsufficientFunds:
        messages.error(request, 'אין לך מספיק מטבעות לרכישה הזו.')
        return redirect('shop')
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('shop')

    message = f'הרכישה של {purchase.item_name} בוצעה בהצלחה.'
    if purchase.delivery_code:
        message = f'{message} קוד השובר שלך: {purchase.delivery_code}'
    messages.success(request, message)
    return redirect('shop')
def cart_item_count(request):
    count = 0
    if request.session.get('cart'):
        count = sum(item['quantity'] for item in request.session['cart'].values())
    return {'cart_items_count': count}

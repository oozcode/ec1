from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from .models import Producto, Categoria, Stock
from .forms import ProductoForm, AgregarAlCarritoForm
from transbank.webpay.webpay_plus.transaction import Transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout

COMMERCE_CODE = '597055555532'
API_KEY_SECRET = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
TRANSACTION_RETURN_URL = 'http://127.0.0.1:8000/transaccion-completa/'

transaction = Transaction()

# Create your views here.

def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

def logout(request):
    if request.method == "POST":
        logout(request)
        return redirect('index') 
    return redirect('index')

def register(request):
    return render(request, 'registro.html')

def nosotros(request):
    return render(request, 'nosotros.html')

def productos_list(request):
    productos = Producto.objects.all()
    form = AgregarAlCarritoForm()

    if 'mensaje' in request.session:
        mensaje = request.session['mensaje']
        del request.session['mensaje']
    else:
        mensaje = None

    return render(request, 'productos_list.html', {'productos': productos, 'form': form, 'mensaje': mensaje})

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    form = AgregarAlCarritoForm(request.POST)

    if form.is_valid():
        cantidad = form.cleaned_data['cantidad']
        carrito = request.session.get('carrito', {})

        if cantidad > producto.stock.cantidad:
            request.session['mensaje'] = f"No puedes agregar más de {producto.stock.cantidad} unidades de {producto.nombre}."
            return redirect('productos')

        if str(producto_id) not in carrito:
            carrito[str(producto_id)] = {'cantidad': 0, 'precio': producto.precio}

        if carrito[str(producto_id)]['cantidad'] + cantidad > producto.stock.cantidad:
            request.session['mensaje'] = f"No puedes agregar más de {producto.stock.cantidad} unidades de {producto.nombre}."
            return redirect('productos')

        carrito[str(producto_id)]['cantidad'] += cantidad
        request.session['carrito'] = carrito
        request.session['mensaje'] = f"Agregaste {cantidad} unidad(es) de {producto.nombre} al carrito."
        return redirect('productos')

    request.session['mensaje'] = "Hubo un problema al agregar el producto al carrito."
    return redirect('productos')

def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    if str(producto_id) in carrito:
        del carrito[str(producto_id)]
        request.session['carrito'] = carrito

    return redirect('ver_carrito')

def vaciar_carrito(request):
    request.session['carrito'] = {}
    return redirect('ver_carrito')

def pagar(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, 'No hay productos en el carrito.')
        return redirect('productos')

    productos_en_carrito = []
    for key, value in carrito.items():
        producto = get_object_or_404(Producto, id=key)
        productos_en_carrito.append({
            'producto': producto,
            'cantidad': value['cantidad'],
            'precio': value['precio'],
            'total': value['cantidad'] * value['precio']
        })

    total_carrito = sum(item['total'] for item in productos_en_carrito)

    transaction = Transaction()
    response = transaction.create(
        buy_order='order12345',
        session_id='session12345',
        amount=total_carrito,
        return_url=TRANSACTION_RETURN_URL
    )
    return redirect(response['url'] + '?token_ws=' + response['token'])

def transaccion_completa(request):
    token_ws = request.GET.get('token_ws') or request.POST.get('token_ws')
    if not token_ws:
        return HttpResponse('Token no encontrado', status=400)

    transaction = Transaction()
    result = transaction.commit(token_ws)
    if result['status'] == 'AUTHORIZED':
        compra_exitosa = {
            'productos': request.session.get('carrito', {}),
            'total': result['amount']
        }
        
        for item_id, item in compra_exitosa['productos'].items():
            producto = get_object_or_404(Producto, id=item_id)
            stock = get_object_or_404(Stock, cod_prod=producto)
            stock.cantidad -= item['cantidad']
            stock.save()
        
        request.session['compra_exitosa'] = compra_exitosa
        request.session['carrito'] = {}  # Limpiar el carrito después de una transacción exitosa
        return redirect('resumen_compra')
    else:
        return HttpResponse(f'Error en la transacción: {result["status"]}')

def resumen_compra(request):
    compra_exitosa = request.session.get('compra_exitosa', {})
    if not compra_exitosa:
        messages.error(request, 'No hay información de compra disponible.')
        return redirect('productos')

    productos_con_totales = []
    for item_id, detalles in compra_exitosa['productos'].items():
        producto = Producto.objects.get(id=item_id)
        total = detalles['cantidad'] * detalles['precio']
        productos_con_totales.append({
            'producto': producto,
            'cantidad': detalles['cantidad'],
            'precio': detalles['precio'],
            'total': total
        })

    compra_exitosa['productos_con_totales'] = productos_con_totales

    return render(request, 'resumen_compra.html', {'compra': compra_exitosa})

def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    productos_en_carrito = []
    for key, value in carrito.items():
        producto = get_object_or_404(Producto, id=key)
        productos_en_carrito.append({
            'producto': producto,
            'cantidad': value['cantidad'],
            'precio': value['precio'],
            'total': value['cantidad'] * value['precio']
        })

    total_carrito = sum(item['total'] for item in productos_en_carrito)
    return render(request, 'carrito.html', {'productos_en_carrito': productos_en_carrito, 'total_carrito': total_carrito})

@user_passes_test(lambda u: u.is_staff)
def productos_list_admin(request):
    productos = Producto.objects.all()
    return render(request, 'prodadmin.html', {'productos': productos})

@login_required
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.save()
            Stock.objects.create(cod_prod=producto, cantidad=form.cleaned_data['cantidad'])
            return redirect('prodadmin')
    else:
        form = ProductoForm()
    return render(request, 'agregar_producto.html', {'form': form})

@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.save()
            stock, created = Stock.objects.get_or_create(cod_prod=producto)
            stock.cantidad = form.cleaned_data['cantidad']
            stock.save()
            return redirect('prodadmin')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'editar_producto.html', {'form': form, 'producto': producto})

@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return redirect('prodadmin')
    return render(request, 'eliminar_producto.html', {'producto': producto})

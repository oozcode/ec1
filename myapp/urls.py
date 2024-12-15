from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.login, name="login"),
    path('registro/', views.register, name="registro"),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('productos/', views.productos_list, name='productos'),
    path('prodAdmin/', views.productos_list_admin, name='prodadmin'),
    path('prodAdmin/agregar/', views.agregar_producto, name='agregar_producto'),
    path('prodAdmin/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('prodAdmin/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    path('pagar/', views.pagar, name='pagar'),
    path('transaccion-completa/', views.transaccion_completa, name='transaccion_completa'),
    path('resumen-compra/', views.resumen_compra, name='resumen_compra'),
    path('logout/', views.logout, name='logout'),
]


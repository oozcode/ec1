from django.db import models
from django.contrib.auth.models import User

# Create your models here

class Categoria(models.Model):
    nombre = models.CharField(max_length = 100)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    cod_prod = models.CharField(max_length = 100, unique = True)
    nombre = models.CharField(max_length = 100)
    descripcion = models.TextField(max_length = 100)
    precio = models.IntegerField()
    precio_usd = models.FloatField(null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete = models.CASCADE, related_name = 'productos')

    def __str__(self):
        return self.nombre
    
class Stock(models.Model):
    cod_prod = models.OneToOneField(Producto, on_delete = models.CASCADE, primary_key = True)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f'Stock de {self.cod_prod.nombre}: {self.cantidad} unidades'

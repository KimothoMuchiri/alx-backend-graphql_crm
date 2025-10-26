from django.db import models
import uuid

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank = True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True,  editable=False)
    name = models.CharField(max_length = 100, null = False)
    price = models.DecimalField(max_digits = 10, decimal_places =2, null = False)
    stock = models.IntegerField(default = 0)

    def __str__(self):
        return self.name

class Order(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True,  editable=False)
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    products = models.ManyToManyField(Product)
    total_amount = models.DecimalField(max_digits=10, decimal_places = 2, default = 0.00)
    order_date = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Order {self.id} for {self.customer.name}"

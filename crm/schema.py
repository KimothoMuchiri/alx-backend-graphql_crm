import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType
from graphene.types import InputObjectType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from .models import Customer, Product, Order
from django.core.validators import RegexValidator
from graphene_django.filter import DjangoFilterConnectionField
from .filters import CustomerFilter, ProductFilter, OrderFilter

# Define a custom Phone Validator for the argument 
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$', # Simple regex for common international format
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

# Define the types that mutations will return
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        field = ("id", "name", "email", "phone", "created_at")
        interfaces = (relay.Node,) 
        filter_fields = ()
        # connection_class = CustomerConnection

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (relay.Node,) 
        filter_fields = ()
        # connection_class = ProductConnection


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount","order_date")
        interfaces = (relay.Node,) 
        filter_fields = ()
        # connection_class = OrderConnection

class CustomerConnection(relay.Connection):
    class Meta:
        # Reference the *string* name of the node type
        node = CustomerType

class ProductConnection(relay.Connection):
    class Meta:
        node = ProductType

class OrderConnection(relay.Connection):
    class Meta:
        node = OrderType

# --- 2. INPUT TYPES (For complex inputs like BulkCreate) ---

class CustomerInput(InputObjectType):
    """Defines the input structure for a single customer in the bulk mutation."""
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class OrderInput(InputObjectType):
    """Input for creating a new Order."""
    # 1. Foreign Key: Customer ID (must exist!)
    customer_id = graphene.ID(required=True) 
    
    # 2. Many-to-Many: A list of Product IDs
    product_ids = graphene.List(graphene.ID, required=True)
    
    # 3. Optional date
    order_date = graphene.DateTime()

# --- 3. MUTATION CLASSES ---

class CreateOrder(graphene.Mutation):
    # Define the output
    order = graphene.Field(OrderType)
    message = graphene.String()

    class Arguments:
        input = OrderInput(required=True)

    def mutate(root, info, input=None):

        customer_id = input.customer_id
        product_ids = input.product_ids
        order_date = input.order_date

        # 1. Input Validation and Fetching
        try:
            # Check if customer exists
            customer = Customer.objects.get(pk=customer_id)
        except ObjectDoesNotExist:
            return CreateOrder(order=None, message=f"Error: Customer ID {customer_id} not found.")

        # Check if products exist and if list is not empty (implicit validation)
        if not product_ids:
            return CreateOrder(order=None, message="Error: Order must contain at least one product.")
        
        products = Product.objects.filter(id__in=product_ids)
        
        # Check if all provided product IDs were valid
        if products.count() != len(product_ids):
            # This is complex, but for simplicity, we'll just return a generic error
            return CreateOrder(order=None, message="Error: One or more product IDs were invalid.")

        # 2. Server-side Calculation of Total Amount
        # sum() needs the values to be cast to float/decimal for calculation
        total_amount = sum(product.price for product in products)
        
        # 3. Create the Order and Relationships
        with transaction.atomic():
            # Create the main Order object
            order = Order.objects.create(
                customer=customer,
                total_amount=total_amount,
                order_date=order_date # Defaults to now if None
            )
            # Save the Many-to-Many relationship
            order.products.set(products) 
        
        # 4. Return Success
        return CreateOrder(order=order, message="Order created successfully with calculated total.")

class CreateProduct(graphene.Mutation):
    # define the output
    product = graphene.Field(ProductType)
    message = graphene.String()

    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required= True)
        stock = graphene.Int()

    def mutate(root, info, name, price, stock=0):
        # 1. Price Validation (Must be positive)
        if price <= 0:
            return CreateProduct(product=None, message="Error: Price must be a positive number.")
        
        # 2. Stock Validation (Must be non-negative)
        if stock < 0:
            return CreateProduct(product=None, message="Error: Stock cannot be negative.")

        # 3. Create the Product using the Django ORM
        try:
            product = Product.objects.create(
                name=name,
                price=price,
                stock=stock
            )
            # 4. Return Success
            return CreateProduct(product=product, message="Product created successfully!")
        
        except Exception as e:
            # Catch any unexpected database or conversion errors
            return CreateProduct(product=None, message=f"Database Error: {str(e)}")        


class CreateCustomer(graphene.Mutation):
    # Define the output
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    # define the input fields
    class Arguments:
        name = graphene.String(required = True)
        email = graphene.String(required = True)
        phone = graphene.String()

    def mutate(root, inf, name, email, phone=None):
        # 1. Check for Duplicates (Email Uniqueness)
        if Customer.objects.filter(email=email).exists():
            # 2. Handle Error: Return the message and a null customer
            return CreateCustomer(customer=None, message=f"Error: Customer with email {email} already exists.")
        
        # 2. Add Phone Validation Check here
        if phone:
            try:
                phone_validator(phone)
            except ValidationError as e:
                # Return the specific error message from the validator
                return CreateCustomer(customer=None, message=f"Error: Phone number invalid. Details: {e.message}")
        
        # 3. Create Object (If unique)
        customer = Customer.objects.create(
            name=name, 
            email=email, 
            phone=phone
        )
        
        # 4. Return Success
        return CreateCustomer(
            customer=customer, 
            message="Customer created successfully!"
        )

class BulkCreateCustomers(graphene.Mutation):
    # Output (Payload) fields
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String) # A list of error strings

    class Arguments:
        # Input is a List of the CustomerInput type
        customers_data = graphene.List(CustomerInput, required=True) 

    def mutate(root, info, customers_data):
        created_customers = []
        errors = []
        
        # Use a transaction to ensure database consistency for the bulk operation
        with transaction.atomic():
            for i, data in enumerate(customers_data):
                email = data.get('email')
                name = data.get('name')
                phone = data.get('phone')

                # Basic Validation: Check for required fields and uniqueness
                if not name:
                    errors.append(f"Record {i}: Name is required.")
                    continue

                if Customer.objects.filter(email=email).exists():
                    errors.append(f"Record {i}: Customer with email {email} already exists.")
                    continue
                
                # If validation passes, create the customer object
                customer = Customer.objects.create(
                    name=name,
                    email=email,
                    phone=phone
                )
                created_customers.append(customer)

        # Return the results
        return BulkCreateCustomers(customers=created_customers, errors=errors)

# --- 4. APP-LEVEL QUERY CLASS ---
class Query(graphene.ObjectType):
    ping = graphene.String() 

    def resolve_ping(root, info):
        return "CRM GraphQL API is up and running!"

    # All customers query
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class = CustomerFilter
    )

    # All products Query
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class = ProductFilter
    )

    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class = OrderFilter
    )


# --- 5. ROOT MUTATION (Combine all mutations) ---

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field() 
    create_order = CreateOrder.Field()
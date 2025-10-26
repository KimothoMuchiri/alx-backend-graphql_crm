import graphene
from graphene_django.types import DjangoObjectType
from graphene.types.input import InputObjectType
from django.db import transaction
from .models import Customer, Product, Order

# Define the types that mutations will return
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        field = ("id", "name", "email", "phone", "created_at")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

# --- 2. INPUT TYPES (For complex inputs like BulkCreate) ---

class CustomerInput(InputObjectType):
    """Defines the input structure for a single customer in the bulk mutation."""
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

# --- 3. MUTATION CLASSES ---
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

# --- 4. ROOT MUTATION (Combine all mutations) ---

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    # create_product = CreateProduct.Field() # These are next!
    # create_order = CreateOrder.Field()
    pass # Remove this when you add more mutations!

# The Query class would go here if you needed app-specific queries



# Client-side Mutations
# mutation CreateNewCustomer($name: String!, $email: String!, $phone: String ) {
#     createCustomer(input: {
#         name: $name,
#         email: $email,
#         phone: $phone
#     }) {
#         # The output field should be 'customer' (or similar), not 'post'
#         customer { 
#             id
#             name
#             email
#             phone
#             createdAt
#         }
#         message # The homework requires a success message output
#     }
# }
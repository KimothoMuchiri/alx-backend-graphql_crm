import django_filters
from django_filters import DateRangeFilter, CharFilter, RangeFilter, Filter
from .models import Customer, Product, Order # Import your models
from django.db.models import Q, CharField

# -----------------
# 1. CUSTOMER FILTER
# -----------------
class CustomerFilter(django_filters.FilterSet):
    # Case-insensitive partial match for name and email
    name = CharFilter(lookup_expr='icontains')
    email = CharFilter(lookup_expr='icontains')

    # Date Range Filter for created_at (gives us __gte and __lte fields automatically)
    created_at = DateRangeFilter()

    # Define the custom filter for phone pattern matching (Challenge)
    phone_pattern = CharFilter(method='filter_by_phone_pattern')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at'] # These are the standard fields we are exposing

        order_by = ['name','email', 'created_at']
        
        # Override the default filter types for CharField and DateField
        filter_overrides = {
            # Use icontains for all CharFields by default (if not explicitly defined above)
            CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                }
            },
        }

    def filter_by_phone_pattern(self, queryset, name, value):
        # 'name' is the field name (phone_pattern), 'value' is the pattern (e.g., '+1')
    
        # Use a Django ORM lookup (__startswith) for efficiency
        return queryset.filter(
            # We are filtering the 'phone' model field using the 'startswith' lookup
            phone__startswith=value 
        )

# -----------------
# 2. PRODUCT FILTER
# -----------------
class ProductFilter(django_filters.FilterSet):
    # Case-insensitive partial match for name
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    # RangeFilter provides both __gte and __lte lookups for price (e.g., price__gte, price__lte)
    price = django_filters.RangeFilter()
    
    # RangeFilter also works well for stock levels
    stock = django_filters.RangeFilter()
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']
        order_by = ['name','price','stock']

        # Ensure icontains is the default for name/char fields
        filter_overrides = {
            CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                }
            },
        }

# -----------------
# 3. ORDER FILTER
# -----------------
class OrderFilter(django_filters.FilterSet):
    # Range Filter for total_amount (__gte and __lte lookups)
    total_amount = django_filters.RangeFilter()
    
    # Date Range Filter for order_date (__gte and __lte lookups)
    order_date = django_filters.DateRangeFilter()
    
    # Filter Orders by Customer Name (Foreign Key Relationship)
    customer_name = django_filters.CharFilter(
        field_name='customer__name',       # Look from Order -> Customer -> name
        lookup_expr='icontains'
    )
    
    # Filter Orders by Product Name (Many-to-Many Relationship)
    product_name = django_filters.CharFilter(
        field_name='products__name',       # Look from Order -> Products -> name
        lookup_expr='icontains'
    )
    # Challenge: Filter orders that contain a specific product ID
    # The 'products__id' lookup works because it looks into the M2M set of the Order
    product_id = django_filters.NumberFilter(
        field_name='products__id',
        lookup_expr='exact'
    )
    
    class Meta:
        model = Order
        fields = ['total_amount', 'order_date'] # These are the direct fields
        order_by = ['total_amount', 'order_date']

        
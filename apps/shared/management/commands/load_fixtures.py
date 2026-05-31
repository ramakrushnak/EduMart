"""Management command to load sample fixtures"""
from django.core.management.base import BaseCommand
from faker import Faker
from apps.accounts.models import User, School
from apps.products.models import Product, ProductCategory
from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from decimal import Decimal
import random
import uuid

fake = Faker(['en_IN'])


class Command(BaseCommand):
    help = 'Load sample data for development and testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading sample data...'))

        # Create schools
        self.stdout.write('Creating schools...')
        schools = []
        school_names = ['Delhi Public School', 'St Xavier School', 'Delhi Convent', 'Birla School', 'Ryan International']
        for name in school_names:
            school, created = School.objects.get_or_create(
                code=name.replace(' ', '').upper()[:10],
                defaults={
                    'name': name,
                    'type': random.choice(['PRIMARY', 'SECONDARY', 'SENIOR']),
                    'email': fake.email(),
                    'phone': fake.phone_number()[:15],
                    'address': fake.address(),
                    'city': random.choice(['Delhi', 'Mumbai', 'Bangalore', 'Chennai']),
                    'state': 'State',
                    'postal_code': fake.postcode(),
                }
            )
            if created:
                schools.append(school)
                self.stdout.write(f'  Created: {school.name}')

        if not schools:
            schools = list(School.objects.all()[:5])

        # Create users
        self.stdout.write('Creating users...')
        users = []
        for i in range(20):
            user, created = User.objects.get_or_create(
                email=f'user{i}@test.com',
                defaults={
                    'username': f'user{i}',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'mobile': fake.phone_number()[:15],
                    'role': random.choice(['STUDENT', 'PARENT', 'SCHOOL_ADMIN']),
                    'school': random.choice(schools),
                    'address': fake.address(),
                    'city': random.choice(['Delhi', 'Mumbai', 'Bangalore']),
                    'is_email_verified': True,
                    'is_mobile_verified': True,
                }
            )
            if created:
                user.set_password('TestPass123')
                user.save()
                users.append(user)
                self.stdout.write(f'  Created: {user.email}')

        if not users:
            users = list(User.objects.filter(role='STUDENT')[:20])

        # Create product categories
        self.stdout.write('Creating product categories...')
        categories_data = [
            ('BAGS', 'School Bags'),
            ('NOTEBOOKS', 'Notebooks'),
            ('PENS', 'Pens'),
            ('UNIFORMS', 'Uniforms'),
            ('TIES', 'Ties'),
            ('BELTS', 'Belts'),
            ('BADGES', 'Badges'),
            ('MEDALS', 'Medals'),
            ('SANITARY', 'Sanitary Items'),
            ('ACCESSORIES', 'Other Accessories'),
        ]

        categories = []
        for idx, (code, name) in enumerate(categories_data):
            category, created = ProductCategory.objects.get_or_create(
                category=code,
                defaults={
                    'name': name,
                    'display_order': idx,
                }
            )
            if created:
                categories.append(category)
                self.stdout.write(f'  Created: {category.name}')

        if not categories:
            categories = list(ProductCategory.objects.all())

        # Create products
        self.stdout.write('Creating products...')
        product_names = {
            'BAGS': ['School Backpack - Blue', 'School Backpack - Black', 'Gym Bag', 'Lunch Bag'],
            'NOTEBOOKS': ['100 Pages Notebook', '200 Pages Notebook', 'Graph Notebook', 'Spiral Notebook'],
            'PENS': ['Blue Pen - Pack of 10', 'Black Pen - Pack of 10', 'Gel Pen - Pack of 5'],
            'UNIFORMS': ['School Shirt', 'School Pants', 'School Skirt'],
            'TIES': ['School Tie - Blue', 'School Tie - Black'],
            'BELTS': ['School Belt - Black', 'School Belt - Brown'],
            'BADGES': ['School Badge', 'House Badge - Red', 'House Badge - Blue'],
            'MEDALS': ['Gold Medal', 'Silver Medal', 'Bronze Medal'],
            'SANITARY': ['Hand Sanitizer', 'Face Mask - Box of 50'],
            'ACCESSORIES': ['School Pin', 'Socks - Pack of 3'],
        }

        products = []
        for category in categories:
            for product_name in product_names.get(category.category, ['Generic Product']):
                product, created = Product.objects.get_or_create(
                    sku=f"SKU-{uuid.uuid4().hex[:8].upper()}",
                    defaults={
                        'category': category,
                        'product_name': product_name,
                        'description': f'High-quality {product_name}',
                        'barcode': f"BAR-{uuid.uuid4().hex[:12].upper()}",
                        'price': Decimal(str(random.randint(50, 2000))),
                        'discount_percentage': Decimal(str(random.randint(0, 20))),
                        'tax_percentage': Decimal('5'),
                        'stock_quantity': random.randint(50, 500),
                        'min_stock_level': 10,
                        'availability_status': 'IN_STOCK',
                    }
                )
                if created:
                    products.append(product)

        self.stdout.write(f'  Created {len(products)} products')

        # Create sample carts
        self.stdout.write('Creating sample carts...')
        for user in users[:10]:
            cart, created = Cart.objects.get_or_create(user=user)
            if created:
                # Add random items
                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)
                    CartItem.objects.get_or_create(
                        cart=cart,
                        product=product,
                        defaults={'quantity': random.randint(1, 3)}
                    )
                self.stdout.write(f'  Created cart for: {user.email}')

        # Create sample orders
        self.stdout.write('Creating sample orders...')
        for user in users[:5]:
            order = Order.objects.create(
                user=user,
                school=user.school,
                status=random.choice(['PENDING', 'CONFIRMED', 'SHIPPED']),
                total_amount=Decimal(str(random.randint(500, 5000))),
                shipping_address=fake.address(),
            )

            # Add order items
            for _ in range(random.randint(1, 3)):
                product = random.choice(products)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 3),
                    unit_price=product.price,
                    discount_percentage=product.discount_percentage,
                    tax_percentage=product.tax_percentage,
                )

            self.stdout.write(f'  Created order for: {user.email}')

        self.stdout.write(self.style.SUCCESS('✅ Sample data loaded successfully!'))

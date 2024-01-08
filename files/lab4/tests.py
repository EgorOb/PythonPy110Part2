from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework import status

from .models import Cart, CartItem
from store.models import Product, Category, Unit, Currency
from .serializers import CartSerializer
from .views import CartViewSet


class CartViewSetTestCase(TestCase):
    """
    Тестирование объекта CartViewSet

    При тестировании проверяем правильность создания объектов, а также
    правильность отрабатывания методов:
        create (test_create_cart_item),
        update (test_update_cart_item),
        delete (test_delete_cart_item).
    """

    def setUp(self):
        """
        Инициализация параметров перед запуском каждого теста (Django очищает БД
        перед каждым тестом, поэтому в начале каждого теста создаются данные
        необходимые для теста)
        """

        # Создание объекта моделирующего отправление запроса
        self.factory = APIRequestFactory()

        # Создание тестового пользователя
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')

        # Создание объектов в БД необходимых для создания продукта в БД
        category = Category.objects.create(name="Овощи", slug_name="vegetables")
        unit = Unit.objects.create(name="кг", description="Килограмм")
        currency = Currency.objects.create(name="руб", description="Рубль")
        # Создание продукта
        self.product = Product.objects.create(
            name="Болгарский перец",
            description='Сочный и яркий, он добавит красок и вкуса в ваши блюда.',
            slug_name='bell_pepper',
            unit=unit,
            quantity_per_unit=1.0,
            price=300.00,
            currency=currency,
            category=category,
        )

    def test_create_cart(self):
        # Проверка, что при создании пользователя автоматически
        # создаётся для него корзина
        cart_exist = Cart.objects.filter(customer=self.user).exists()
        self.assertTrue(cart_exist, "Корзина не создалась автоматически")

    def test_create_cart_item(self):
        # Отправляем запрос на адрес /carts/ с данными
        cart = Cart.objects.get(customer=self.user)
        request = self.factory.post('/carts/', {'product': self.product.id,
                                                'cart': cart.id})
        # Записываем пользователя в запрос (имитирование действия промежуточного ПО в Django)
        request.user = self.user
        # Инициализуем вызов POST запроса в представлении
        view = CartViewSet.as_view({'post': 'create'})
        # Передаём запрос в представление и получаем результат от этого представления
        response = view(request)
        # Проводим проверки тех действий, что сделало представление
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Продукт успешно добавлен в корзину')
        self.assertEqual(CartItem.objects.count(), 1)

    def test_update_cart_item(self):
        cart = Cart.objects.get(customer=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product)
        request = self.factory.put(f'/carts/{cart_item.id}/', {'quantity': 5})
        request.user = self.user
        view = CartViewSet.as_view({'put': 'update'})

        response = view(request, pk=cart_item.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Данные объекта корзины изменены')

        cart_item.refresh_from_db()
        # Изменение было внесено непосредственно в базу данных, а не в объект
        # Python, refresh_from_db() гарантирует, что объект cart_item отобразит
        # актуальные данные из базы данных, что важно для правильного
        # проведения последующих проверок в вашем тесте.
        self.assertEqual(cart_item.quantity, 5)

    def test_delete_cart_item(self):
        cart = Cart.objects.get(customer=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product)
        request = self.factory.delete(f'/carts/{cart_item.id}/')
        request.user = self.user
        view = CartViewSet.as_view({'delete': 'destroy'})

        response = view(request, pk=cart_item.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Продукт успешно удалён из корзины')
        self.assertEqual(CartItem.objects.count(), 0)


class CartSerializerTestCase(TestCase):
    """
    Пример проверки сериализатора
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             password='testpassword')
        category = Category.objects.create(name="Овощи", slug_name="vegetables")
        unit = Unit.objects.create(name="кг", description="Килограмм")
        currency = Currency.objects.create(name="руб", description="Рубль")
        self.product = Product.objects.create(
            name="Болгарский перец",
            description='Сочный и яркий, он добавит красок и вкуса в ваши блюда.',
            slug_name='bell_pepper',
            unit=unit,
            quantity_per_unit=1.0,
            price=300.00,
            currency=currency,
            category=category,
        )
        self.cart = Cart.objects.get(customer=self.user)

        self.cart_item = CartItem.objects.create(cart=self.cart,
                                                 product=self.product)

    def test_cart_serializer(self):
        serializer = CartSerializer(instance=self.cart_item)
        expected_data = {
            'id': self.cart_item.id,
            'cart': self.cart.id,
            'quantity': self.cart_item.quantity,
            'product': self.product.id,
        }
        # Проверка, что на выходе сериализатора данные соответствуют нужным.
        # На самом деле в serializer.data данных больше чем нужно, поэтому
        # используется self.assertDictContainsSubset для проверки вхождения
        # одного словаря в другой
        self.assertDictContainsSubset(expected_data, serializer.data)

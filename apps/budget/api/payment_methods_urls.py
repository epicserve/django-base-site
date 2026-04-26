from django.urls import path

from .views import PaymentMethodDetailAPIView, PaymentMethodListAPIView

urlpatterns = [
    path("", PaymentMethodListAPIView.as_view(), name="payment-method-list"),
    path("<int:pk>/", PaymentMethodDetailAPIView.as_view(), name="payment-method-detail"),
]

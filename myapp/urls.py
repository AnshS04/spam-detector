from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('report-spam/', views.report_spam, name='report_spam'),
    path('addContact/', views.add_contact, name='add_contact'),
    path('search/', views.search_contacts, name='search_contacts'),
    path('searchNumber/', views.search_by_phone_number, name='search_by_phone_number'),
    path('getDetails/', views.get_details, name='get_details'),
]

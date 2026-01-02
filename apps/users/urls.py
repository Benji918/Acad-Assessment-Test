from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import UserRegistrationView, UserProfileView, CustomLogoutView

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', CustomLogoutView.as_view(), name='user-logout'),
]
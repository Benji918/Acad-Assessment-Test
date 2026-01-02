from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, UserSerializer
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.utils import blacklist_token
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError


logger = logging.getLogger(__name__)

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    '''API endpoint for user registration.'''

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'success': True,
            'message': 'User registered successfully',
            'data': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    '''API endpoint for retrieving and updating user profile.'''

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user



@extend_schema(
    # request={
    #     'application/json': {
    #         'type': 'object',
    #         'properties': {
    #             'refresh': {
    #                 'type': 'string',
    #                 'description': 'Refresh token (optional - will fall back to cookie if not provided)',
    #                 'required': True
    #             }
    #         }
    #     }
    # },
    parameters=[
        OpenApiParameter(
            name="refresh",
            location=OpenApiParameter.QUERY,
            required=True,
            type=str,
            description="Refresh token."
        )
    ],
)
class CustomLogoutView(APIView):
    """Enhanced logout view"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        errors = []

        refresh_token = request.GET.get('refresh')

        if not refresh_token:
            return Response(
                {"success": False,
                 "message": "Refresh token missing.",
                 },status=status.HTTP_400_BAD_REQUEST
            )


        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info("Refresh token blacklisted via SimpleJWT for user=%s", request.user.email)
            except TokenError as e:
                errors.append(f"Refresh token error: {str(e)}")
                logger.error("Refresh token error for user=%s: %s", request.user.email, str(e))

            auth = request.META.get("HTTP_AUTHORIZATION", "")
            if auth and auth.split()[0].lower() == "bearer":
                access_token = auth.split()[1].strip()
                try:
                    ttl = blacklist_token(access_token)
                    logger.info("Access token blacklisted ttl=%s for user=%s", ttl, request.user.email)
                except Exception as exc:
                    logger.exception("Failed to blacklist access token: %s", exc)
                    errors.append("Failed to blacklist access token")
        else:
            errors.append("No refresh token provided in payload or cookie")
            logger.warning("No refresh token found for user=%s", request.user.email)


        if errors:
            return Response(
                {"success": False,
                 "message": "Logout completed with errors.",
                 "data": errors
                 },status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(
            {'success': True, 'message': 'Logout successful.'},
            status=status.HTTP_200_OK
        )

        logger.info(f"User logged out: {request.user.email}")

        return response
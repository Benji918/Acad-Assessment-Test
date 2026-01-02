from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from core.validators import sanitize_email
from types import SimpleNamespace
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    '''Serializer for user registration with password validation.'''
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password2', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if not sanitize_email(attrs['email']):
            raise serializers.ValidationError({'email': 'Email address is invalid. Please check the format'})

        user =  User(
            email=attrs.get("email"),
            username=attrs.get("username"),
            first_name=attrs.get("first_name"),
            last_name=attrs.get("last_name"),
        )

        password = attrs["password"]

        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        return user

class UserSerializer(serializers.ModelSerializer):
    '''Serializer for user details.'''

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'full_name', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')
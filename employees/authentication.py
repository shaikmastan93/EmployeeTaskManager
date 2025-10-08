# employees/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils import timezone

class CustomJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT's authentication to reject tokens issued before the user's
    password_changed_at timestamp (so old tokens become invalid after password change).
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        # token has 'iat' field (issued at) as int (seconds)
        token_iat = validated_token.get('iat')
        if token_iat is None:
            return user

        try:
            profile = user.profile
            pwd_changed = profile.password_changed_at
            # convert to seconds and compare
            token_iat_dt = timezone.datetime.fromtimestamp(token_iat, tz=timezone.utc)
            if token_iat_dt < pwd_changed:
                raise AuthenticationFailed('Token was issued before the last password change. Please login again.')
        except AttributeError:
            # if no profile, allow
            pass

        return user

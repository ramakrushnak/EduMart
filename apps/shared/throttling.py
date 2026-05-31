from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class CustomAnonRateThrottle(AnonRateThrottle):
    pass


class CustomUserRateThrottle(UserRateThrottle):
    pass
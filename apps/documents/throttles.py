from rest_framework.throttling import ScopedRateThrottle


class CollabTokenThrottle(ScopedRateThrottle):
    scope = "collab_token"


class InviteCreateThrottle(ScopedRateThrottle):
    scope = "invite_create"

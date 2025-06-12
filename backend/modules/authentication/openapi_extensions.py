from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class ClerkAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'modules.authentication.clerk_auth.ClerkAuthentication'
    name = 'ClerkAuth'
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Clerk JWT authentication. Use format: Bearer <token>'
        }

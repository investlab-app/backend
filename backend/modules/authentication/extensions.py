from drf_spectacular.extensions import OpenApiAuthenticationExtension

class ClerkAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'modules.authentication.clerk_auth.ClerkAuthentication'
    name = 'ClerkJWT'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme.',
        }

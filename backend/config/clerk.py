from clerk_backend_api import Clerk

from .settings import CLERK_SECRET_KEY

client = Clerk(bearer_auth=CLERK_SECRET_KEY)

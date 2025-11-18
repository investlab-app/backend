import logging

from config.clients import clerk_client as clerk_sdk

logger = logging.getLogger(__name__)


class ClerkUserService:
    def get_user_email_addresses(self, clerk_id: str) -> list[str]:
        try:
            user = clerk_sdk.users.get(user_id=clerk_id)
            if not user:
                return []
            return [email.email_address for email in user.email_addresses]
        except Exception:
            logger.exception("Failed to get email addresses for user %s", clerk_id)
            return []

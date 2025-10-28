class CommandMessagesMixin:
    def print_success(self, message: str):
        self.stdout.write(self.style.SUCCESS(message))

    def print_error(self, message: str):
        self.stdout.write(self.style.ERROR(message))

    def print_warning(self, message: str):
        self.stdout.write(self.style.WARNING(message))

    def print_info(self, message: str):
        self.stdout.write(self.style.NOTICE(message))

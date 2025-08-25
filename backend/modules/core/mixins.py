
from modules.core.utils import get_attr


class UpdateWithMappingMixin:
    EDITABLE_FIELDS_MAPPING: dict[str, str] = {}

    def update_with_mapping[T](self, target: T, source) -> tuple[T, bool]:
        """Update existing model instance with new data based on the mapping."""
        updated = False
        for data_field, model_field in self.EDITABLE_FIELDS_MAPPING.items():
            new_value = get_attr(source, data_field)
            if getattr(target, model_field) != new_value:
                setattr(target, model_field, new_value)
                updated = True
        return target, updated


class CreateWithMappingMixin:
    CREATABLE_FIELDS_MAPPING: dict[str, str] = {}

    def create_with_mapping[T](self, source, target_class: type[T]) -> T:
        """Create a new model instance from the provided data based on the mapping."""
        return target_class(
            **{
                target_field: get_attr(source, source_field)
                for source_field, target_field in self.CREATABLE_FIELDS_MAPPING.items()
            }
        )

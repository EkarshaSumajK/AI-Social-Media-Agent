"""Custom SQLAlchemy types for handling database enum mismatches."""
from sqlalchemy import TypeDecorator, Enum as SQLEnum
from typing import Any


class UpperCaseEnum(TypeDecorator):
    """A type that converts Python enum values to uppercase for PostgreSQL."""
    
    impl = SQLEnum
    cache_ok = True
    
    def __init__(self, enum_class, **kwargs):
        self.enum_class = enum_class
        # Create enum with uppercase values
        uppercase_values = [e.value.upper() for e in enum_class]
        super().__init__(*uppercase_values, **kwargs)
    
    def process_bind_param(self, value: Any, dialect) -> Any:
        """Convert to uppercase when saving to database."""
        if value is not None:
            if hasattr(value, 'value'):
                return value.value.upper()
            return str(value).upper()
        return value
    
    def process_result_value(self, value: Any, dialect) -> Any:
        """Convert from uppercase when reading from database."""
        if value is not None:
            # Find the matching enum member (case-insensitive)
            for member in self.enum_class:
                if member.value.upper() == value.upper():
                    return member
        return value

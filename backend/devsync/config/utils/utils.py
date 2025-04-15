import functools
from typing import (
    Mapping,
    TypeVar,
    Any,
    Callable,
    ParamSpec,
    Union,
    Iterable,
    TypeAlias, cast,
)

PS = ParamSpec("PS")
T = TypeVar("T", bound=Union[Mapping[str, Any], Iterable[Any]])
SensitiveData: TypeAlias = Union[dict[str, Any], list[Any], str]


def sensitive_filter(
    data: T,
    sensitive_keys: Iterable[str],
    *,
    placeholder: str = "***",
) -> T:
    """
    Recursively filters sensitive information from data structures.

    Args:
        data: Input data to be filtered (dict, list, or str)
        sensitive_keys: Keys or substrings to be filtered out
        placeholder: Replacement string for sensitive data

    Returns:
        Filtered data with the same type as input
    """
    if isinstance(data, str):
        return cast(T, _filter_string(data, sensitive_keys, placeholder))
    if isinstance(data, Mapping):
        return cast(T, _filter_mapping(data, sensitive_keys, placeholder))
    if isinstance(data, Iterable):
        return cast(T, _filter_iterable(data, sensitive_keys, placeholder))
    return data


def _filter_string(
    data: str,
    sensitive_keys: Iterable[str],
    placeholder: str,
) -> str:
    """Filter sensitive substrings from a string."""
    for key in sensitive_keys:
        if key in data:
            return placeholder
    return data


def _filter_mapping(
    data: Mapping[str, Any],
    sensitive_keys: Iterable[str],
    placeholder: str,
) -> Mapping[str, Any]:
    """Recursively filter sensitive keys from a mapping."""
    filtered_data: dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive_key(key, sensitive_keys):
            filtered_data[key] = placeholder
        elif isinstance(value, (Mapping, Iterable)):
            filtered_data[key] = sensitive_filter(value, sensitive_keys, placeholder=placeholder)
        else:
            filtered_data[key] = value
    return filtered_data


def _filter_iterable(
        data: Iterable[Any],
        sensitive_keys: Iterable[str],
        placeholder: str,
) -> Iterable[Any]:
    """Recursively filter sensitive data from an iterable."""
    return [sensitive_filter(item, sensitive_keys, placeholder=placeholder) for item in data]


def _is_sensitive_key(key: str, sensitive_keys: Iterable[str]) -> bool:
    """Check if a key contains any sensitive substring (case-insensitive)."""
    key_lower = key.lower()
    return any(sensitive_key.lower() in key_lower for sensitive_key in sensitive_keys)


def apply_sensitive_filter(
        sensitive_keys: Iterable[str],
        *,
        placeholder: str = "***",
) -> Callable[[Callable[PS, T]], Callable[PS, T]]:
    """
    Decorator factory to apply sensitive data filtering to function outputs.

    Args:
        sensitive_keys: Keys or substrings to be filtered out
        placeholder: Replacement string for sensitive data

    Returns:
        Decorator that processes function output
    """

    def decorator(function: Callable[PS, T]) -> Callable[PS, T]:
        @functools.wraps(function)
        def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> T:
            result = function(*args, **kwargs)
            return sensitive_filter(result, sensitive_keys, placeholder=placeholder)

        return wrapper

    return decorator

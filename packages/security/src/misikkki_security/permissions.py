from __future__ import annotations


class PermissionError(ValueError):
    pass


_BLOCKED_PERMISSIONS = {"withdraw", "withdrawal", "transfer", "internal_transfer"}


def assert_no_withdrawal_permissions(permissions: set[str] | list[str] | tuple[str, ...]) -> None:
    normalized = {permission.lower().strip() for permission in permissions}
    blocked = normalized & _BLOCKED_PERMISSIONS
    if blocked:
        blocked_list = ", ".join(sorted(blocked))
        raise PermissionError(f"Withdrawal or transfer permissions are not allowed in MVP: {blocked_list}")

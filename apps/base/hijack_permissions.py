def staff_only(*, hijacker, hijacked):
    if hijacker.is_superuser:
        return True
    return hijacker.is_staff and not hijacked.is_superuser

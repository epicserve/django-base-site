def superuser_only(*, hijacker, hijacked):
    return hijacker.is_superuser and not hijacked.is_superuser

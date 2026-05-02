from . import session


def organization(request):
    org = getattr(request, "org", None)
    org_member_count = session.get_member_count(request)
    org_owner_count = session.get_owner_count(request)

    return {
        "org": org,
        "org_member_count": org_member_count,
        "org_owner_count": org_owner_count,
    }

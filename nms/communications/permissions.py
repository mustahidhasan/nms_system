from rest_framework import permissions
from .models import TeamMembership, Team


class IsSystemAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


def get_membership(user, team: Team):
    if not user or not user.is_authenticated:
        return None
    try:
        return TeamMembership.objects.get(team=team, user=user)
    except TeamMembership.DoesNotExist:
        return None


def user_can_manage_team(user, team: Team):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    membership = get_membership(user, team)
    return bool(membership and membership.role == TeamMembership.Role.TEAM_ADMIN)


def user_in_team(user, team: Team):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return TeamMembership.objects.filter(team=team, user=user).exists()

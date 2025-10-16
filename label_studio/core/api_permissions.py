import logging
from rest_framework.permissions import SAFE_METHODS, BasePermission

logger = logging.getLogger(__name__)


class HasObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        logger.warning(
            f'[RBAC-DEBUG] HasObjectPermission ENTRY: '
            f'user={user.id if user else None} ({user.email if user else "anonymous"}), '
            f'object={obj.__class__.__name__}(id={obj.id}), '
            f'method={request.method}, '
            f'path={request.path}, '
            f'has_permission_method_exists={hasattr(obj, "has_permission")}'
        )

        result = obj.has_permission(user)

        logger.warning(
            f'[RBAC-DEBUG] HasObjectPermission RESULT: '
            f'user={user.id if user else None} ({user.email if user else "anonymous"}), '
            f'object={obj.__class__.__name__}(id={obj.id}), '
            f'result={result}'
        )

        if not result:
            logger.error(
                f'[RBAC-DEBUG] HasObjectPermission DENIED FINAL: '
                f'user={user.id if user else None} ({user.email if user else "anonymous"}), '
                f'object={obj.__class__.__name__}(id={obj.id}), '
                f'method={request.method}, '
                f'path={request.path}'
            )

        return result


class MemberHasOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS and not request.user.own_organization:
            return False

        return obj.has_permission(request.user)

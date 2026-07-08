# Developer Guidelines - MW Visto Backend

This file contains the strict coding style, architectural structure, and patterns that all AI agents and human developers must follow without exception when working on this backend.

## Architectural Patterns & Code Organization

1. **Strict Folder-Based Modular Codebase:**
   - Every Django app must partition its elements into dedicated directories: `models/`, `serializers/`, `views/`, `filters/`, `services/`, `tasks/`.
   - Never write single monolithic files (e.g. do NOT put multiple model classes in a single `models.py` file, or multiple serializer classes in `serializers.py`).
   - Every model, serializer, view, filter, and task must have **its own file** named after the class/domain in snake_case (e.g., `inspection.py`, `step.py`).
   - Standardize exports using `__init__.py` files inside these directories to expose the entities clearly.

2. **Django & DRF Standards:**
   - Models that support soft deletion must inherit from `core.mixins.soft_delete.SoftDeleteModelMixin`.
   - Admin panels for soft-delete models must inherit from `core.mixins.soft_delete_admin.SoftDeleteAdminMixin`.
   - Viewsets that support soft deletion must inherit from `core.mixins.soft_delete.SoftDeleteViewSetMixin`.
   - Nested models creation/updates must use `drf_writable_nested.serializers.WritableNestedModelSerializer`.
   - All models/views must respect multi-tenancy scoping. Scoped models must inherit from `shared_auth.mixins.OrganizationUserMixin` or `TimestampedMixin`, and views should restrict querysets accordingly (e.g. using `IsSameOrganization` permission and filtering querysets).
   - Use `django-filter` and custom filter classes inheriting from `filters.FilterSet` for search capabilities.

3. **Tooling & Environment Configuration:**
   - Use `python-decouple` (`config()`) to read configuration variables from `.env`. Never hardcode secrets.
   - Run lints/formatting via Ruff: `ruff check` and `ruff format`.

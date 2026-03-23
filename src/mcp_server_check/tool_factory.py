"""Declarative tool factory for generating CRUD tools from resource definitions.

Eliminates the repeated `if field is not None: body["field"] = field` boilerplate
by generating list/get/create/update/delete tool functions from a compact schema.

Usage:
    from mcp_server_check.tool_factory import Resource, Field, generate_tools

    resource = Resource(
        name="benefits",
        path="/benefits",
        id_param="benefit_id",
        id_description="The Check benefit ID.",
        description="employee benefits",
        list_filters=["company", "employee"],
        fields=[
            Field("employee", str, required_for="create", doc="The Check employee ID."),
            Field("company_benefit", str, required_for="create", doc="The company benefit ID."),
            Field("description", str, doc="Benefit description."),
            Field("effective_start", str, doc="Start date (YYYY-MM-DD)."),
        ],
    )

    tools = generate_tools(resource)
    # tools.list_fn, tools.get_fn, tools.create_fn, tools.update_fn, tools.delete_fn
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any

from mcp_server_check.helpers import (
    Ctx,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


@dataclass
class Field:
    """A field in a resource schema.

    Attributes:
        name: API field name (e.g. "employee", "description").
        type: Python type annotation (str, int, float, bool, dict, list[str], etc.).
        required_for: If "create", this field is required in the create tool.
            If None, the field is optional for both create and update.
        doc: Documentation string for this field.
        create_only: If True, this field only appears on create, not update.
        update_only: If True, this field only appears on update, not create.
    """

    name: str
    type: type = str
    required_for: str | None = None
    doc: str = ""
    create_only: bool = False
    update_only: bool = False


@dataclass
class Resource:
    """Declarative definition of a Check API resource.

    Attributes:
        name: Resource name in plural form (e.g. "benefits", "pay_schedules").
        path: API path prefix (e.g. "/benefits", "/pay_schedules").
        id_param: Name of the ID parameter (e.g. "benefit_id").
        id_description: Doc string for the ID parameter.
        description: Human-readable description of what this resource is.
        fields: List of Field definitions.
        list_filters: Names of query-parameter fields for list filtering
            (e.g. ["company", "employee"]).
        has_delete: Whether to generate a delete tool. Default True.
        default_limit: Default page size for the list tool. When set, the
            generated list function uses this as the default value for ``limit``
            instead of ``None``, reducing pagination round-trips.
        list_doc: Custom docstring for the list tool.
        get_doc: Custom docstring for the get tool.
        create_doc: Custom docstring for the create tool.
        update_doc: Custom docstring for the update tool.
        delete_doc: Custom docstring for the delete tool.
    """

    name: str
    path: str
    id_param: str
    id_description: str = ""
    description: str = ""
    fields: list[Field] = dataclass_field(default_factory=list)
    list_filters: list[str] = dataclass_field(default_factory=list)
    has_delete: bool = True
    default_limit: int | None = None
    list_doc: str | None = None
    get_doc: str | None = None
    create_doc: str | None = None
    update_doc: str | None = None
    delete_doc: str | None = None


@dataclass
class GeneratedTools:
    """Container for generated tool functions."""

    list_fn: Any = None
    get_fn: Any = None
    create_fn: Any = None
    update_fn: Any = None
    delete_fn: Any = None

    def all_read(self) -> list:
        """Return all read-only tool functions."""
        return [fn for fn in [self.list_fn, self.get_fn] if fn is not None]

    def all_write(self) -> list:
        """Return all write tool functions."""
        return [
            fn
            for fn in [self.create_fn, self.update_fn, self.delete_fn]
            if fn is not None
        ]

    def all(self) -> list:
        """Return all tool functions."""
        return self.all_read() + self.all_write()


def _build_body(fields: list[Field], kwargs: dict, *, is_create: bool) -> dict:
    """Build a request body from field definitions and keyword arguments.

    For create: includes required fields unconditionally, optional fields if not None.
    For update: includes all non-None fields.
    """
    body: dict = {}
    for f in fields:
        if is_create and f.update_only:
            continue
        if not is_create and f.create_only:
            continue
        val = kwargs.get(f.name)
        if is_create and f.required_for == "create":
            body[f.name] = val
        elif val is not None:
            body[f.name] = val
    return body


def _build_params(filter_names: list[str], kwargs: dict) -> dict | None:
    """Build query parameters from filter field names and keyword arguments."""
    params: dict = {}
    for name in filter_names:
        val = kwargs.get(name)
        if val is not None:
            if isinstance(val, list):
                params[name] = ",".join(val)
            elif isinstance(val, bool):
                params[name] = str(val).lower()
            else:
                params[name] = val
    # Standard pagination params
    if kwargs.get("limit") is not None:
        params["limit"] = kwargs["limit"]
    if kwargs.get("cursor"):
        params["cursor"] = kwargs["cursor"]
    return params or None


def _make_list_docstring(res: Resource) -> str:
    """Generate a docstring for a list tool."""
    if res.list_doc:
        return res.list_doc
    filters = ", ".join(res.list_filters) if res.list_filters else "no filters"
    return f"List {res.description}, optionally filtered by {filters}."


def _make_get_docstring(res: Resource) -> str:
    if res.get_doc:
        return res.get_doc
    return f"Get details for a specific {res.description.rstrip('s')}."


def _make_create_docstring(res: Resource) -> str:
    if res.create_doc:
        return res.create_doc
    return f"Create a new {res.description.rstrip('s')}."


def _make_update_docstring(res: Resource) -> str:
    if res.update_doc:
        return res.update_doc
    return f"Update an existing {res.description.rstrip('s')}."


def _make_delete_docstring(res: Resource) -> str:
    if res.delete_doc:
        return res.delete_doc
    return f"Delete a {res.description.rstrip('s')}."


def _build_args_doc(fields: list[Field], extra: dict[str, str] | None = None) -> str:
    """Build the Args: section of a docstring from field definitions."""
    lines = []
    if extra:
        for name, doc in extra.items():
            lines.append(f"    {name}: {doc}")
    for f in fields:
        if f.doc:
            lines.append(f"    {f.name}: {f.doc}")
    return "\n".join(lines)


def generate_tools(res: Resource) -> GeneratedTools:
    """Generate list/get/create/update/delete tool functions from a Resource definition."""
    tools = GeneratedTools()

    # --- list ---
    filter_fields = res.list_filters

    async def _list_fn(
        ctx: Ctx,
        limit: int | None = None,
        cursor: str | None = None,
        **kwargs: Any,
    ) -> dict:
        params = _build_params(
            filter_fields, {**kwargs, "limit": limit, "cursor": cursor}
        )
        return await check_api_list(ctx, res.path, params=params)

    # Build the actual function with proper parameter annotations
    # We need to dynamically create functions with the right signatures
    # for FastMCP's introspection to work properly
    list_fn = _create_list_function(res, filter_fields)
    list_fn.__name__ = f"list_{res.name}"
    list_fn.__qualname__ = f"list_{res.name}"
    tools.list_fn = list_fn

    # --- get ---
    async def _get_fn(ctx: Ctx, **kwargs: Any) -> dict:
        id_val = kwargs[res.id_param]
        return await check_api_get(ctx, f"{res.path}/{id_val}")

    get_fn = _create_get_function(res)
    get_fn.__name__ = f"get_{res.name.rstrip('s')}"
    get_fn.__qualname__ = f"get_{res.name.rstrip('s')}"
    tools.get_fn = get_fn

    # --- create ---
    create_fields = [f for f in res.fields if not f.update_only]
    create_fn = _create_create_function(res, create_fields)
    create_fn.__name__ = f"create_{res.name.rstrip('s')}"
    create_fn.__qualname__ = f"create_{res.name.rstrip('s')}"
    tools.create_fn = create_fn

    # --- update ---
    update_fields = [f for f in res.fields if not f.create_only]
    update_fn = _create_update_function(res, update_fields)
    update_fn.__name__ = f"update_{res.name.rstrip('s')}"
    update_fn.__qualname__ = f"update_{res.name.rstrip('s')}"
    tools.update_fn = update_fn

    # --- delete ---
    if res.has_delete:
        delete_fn = _create_delete_function(res)
        delete_fn.__name__ = f"delete_{res.name.rstrip('s')}"
        delete_fn.__qualname__ = f"delete_{res.name.rstrip('s')}"
        tools.delete_fn = delete_fn

    return tools


def _create_list_function(res: Resource, filter_fields: list[str]):
    """Create a list function with proper type annotations for FastMCP."""
    # Build parameter annotations dict
    annotations: dict[str, Any] = {"ctx": Ctx, "return": dict}
    defaults: dict[str, Any] = {}
    filter_docs: dict[str, str] = {}

    for fname in filter_fields:
        # Find the field doc from resource fields
        field_def = next((f for f in res.fields if f.name == fname), None)
        annotations[fname] = str | None
        defaults[fname] = None
        if field_def and field_def.doc:
            filter_docs[fname] = field_def.doc
        else:
            filter_docs[fname] = f'Filter by {fname} (e.g. "{fname}_xxxxx").'

    limit_default = res.default_limit
    if limit_default is not None:
        annotations["limit"] = int
        defaults["limit"] = limit_default
        filter_docs["limit"] = (
            f"Maximum number of results to return (max {limit_default}, default {limit_default})."
        )
    else:
        annotations["limit"] = int | None
        defaults["limit"] = None
        filter_docs["limit"] = "Maximum number of results to return."
    annotations["cursor"] = str | None
    defaults["cursor"] = None
    filter_docs["cursor"] = "Pagination cursor from a previous response."

    path = res.path

    async def list_fn(ctx: Ctx, **kwargs: Any) -> dict:
        params = _build_params(filter_fields, kwargs)
        return await check_api_list(ctx, path, params=params)

    # Apply annotations and docstring
    list_fn.__annotations__ = annotations
    list_fn.__doc__ = _make_list_docstring(res)
    args_doc = _build_args_doc([], filter_docs)
    if args_doc:
        list_fn.__doc__ += f"\n\nArgs:\n{args_doc}"

    # Set defaults via __defaults__ and __kwdefaults__
    # FastMCP uses inspect.signature, so we need proper defaults
    import inspect

    # Build new parameter list
    params_list = [
        inspect.Parameter(
            "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Ctx
        )
    ]
    for pname in filter_fields:
        params_list.append(
            inspect.Parameter(
                pname,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation=str | None,
            )
        )
    if limit_default is not None:
        params_list.append(
            inspect.Parameter(
                "limit",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=limit_default,
                annotation=int,
            )
        )
    else:
        params_list.append(
            inspect.Parameter(
                "limit",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation=int | None,
            )
        )
    params_list.append(
        inspect.Parameter(
            "cursor",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=None,
            annotation=str | None,
        )
    )
    list_fn.__signature__ = inspect.Signature(params_list, return_annotation=dict)

    return list_fn


def _create_get_function(res: Resource):
    """Create a get function with proper type annotations."""
    import inspect

    path = res.path
    id_param = res.id_param

    async def get_fn(ctx: Ctx, **kwargs: Any) -> dict:
        return await check_api_get(ctx, f"{path}/{kwargs[id_param]}")

    get_fn.__doc__ = _make_get_docstring(res)
    args_doc = f"    {id_param}: {res.id_description}"
    get_fn.__doc__ += f"\n\nArgs:\n{args_doc}"

    params_list = [
        inspect.Parameter(
            "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Ctx
        ),
        inspect.Parameter(
            id_param, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str
        ),
    ]
    get_fn.__signature__ = inspect.Signature(params_list, return_annotation=dict)
    get_fn.__annotations__ = {"ctx": Ctx, id_param: str, "return": dict}
    return get_fn


def _create_create_function(res: Resource, fields: list[Field]):
    """Create a create function with proper type annotations."""
    import inspect

    path = res.path
    field_list = fields  # Capture for closure

    async def create_fn(ctx: Ctx, **kwargs: Any) -> dict:
        body = _build_body(field_list, kwargs, is_create=True)
        return await check_api_post(ctx, path, data=body)

    create_fn.__doc__ = _make_create_docstring(res)
    args_doc = _build_args_doc(fields)
    if args_doc:
        create_fn.__doc__ += f"\n\nArgs:\n{args_doc}"

    params_list = [
        inspect.Parameter(
            "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Ctx
        )
    ]
    ann: dict[str, Any] = {"ctx": Ctx, "return": dict}
    for f in fields:
        if f.required_for == "create":
            params_list.append(
                inspect.Parameter(
                    f.name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=f.type,
                )
            )
            ann[f.name] = f.type
        else:
            params_list.append(
                inspect.Parameter(
                    f.name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=None,
                    annotation=f.type | None,
                )
            )
            ann[f.name] = f.type | None
    create_fn.__signature__ = inspect.Signature(params_list, return_annotation=dict)
    create_fn.__annotations__ = ann
    return create_fn


def _create_update_function(res: Resource, fields: list[Field]):
    """Create an update function with proper type annotations."""
    import inspect

    path = res.path
    id_param = res.id_param
    field_list = fields

    async def update_fn(ctx: Ctx, **kwargs: Any) -> dict:
        id_val = kwargs.pop(id_param)
        body = _build_body(field_list, kwargs, is_create=False)
        return await check_api_patch(ctx, f"{path}/{id_val}", data=body)

    update_fn.__doc__ = _make_update_docstring(res)
    extra = {id_param: res.id_description}
    args_doc = _build_args_doc(fields, extra)
    if args_doc:
        update_fn.__doc__ += f"\n\nArgs:\n{args_doc}"

    params_list = [
        inspect.Parameter(
            "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Ctx
        ),
        inspect.Parameter(
            id_param, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str
        ),
    ]
    ann: dict[str, Any] = {"ctx": Ctx, id_param: str, "return": dict}
    for f in fields:
        params_list.append(
            inspect.Parameter(
                f.name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation=f.type | None,
            )
        )
        ann[f.name] = f.type | None
    update_fn.__signature__ = inspect.Signature(params_list, return_annotation=dict)
    update_fn.__annotations__ = ann
    return update_fn


def _create_delete_function(res: Resource):
    """Create a delete function with proper type annotations."""
    import inspect

    path = res.path
    id_param = res.id_param

    async def delete_fn(ctx: Ctx, **kwargs: Any) -> dict:
        return await check_api_delete(ctx, f"{path}/{kwargs[id_param]}")

    delete_fn.__doc__ = _make_delete_docstring(res)
    args_doc = f"    {id_param}: {res.id_description}"
    delete_fn.__doc__ += f"\n\nArgs:\n{args_doc}"

    params_list = [
        inspect.Parameter(
            "ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Ctx
        ),
        inspect.Parameter(
            id_param, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str
        ),
    ]
    delete_fn.__signature__ = inspect.Signature(params_list, return_annotation=dict)
    delete_fn.__annotations__ = {"ctx": Ctx, id_param: str, "return": dict}
    return delete_fn

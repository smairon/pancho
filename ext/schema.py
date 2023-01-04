import sqlalchemy
from sqlalchemy_schema_factory import factory

db_metadata = factory.metadata()

author = factory.actions_tracked_table(
    name="authors",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.string(name="first_name", nullable=False),
        factory.string(name="last_name", nullable=False),
        factory.datetime(name="birth_date", nullable=False),
        factory.foreign_key(on_="departments.id", name="department_id", nullable=False)
    ),
)

department = factory.actions_tracked_table(
    name="departments",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.string(name="name", nullable=False),
        factory.foreign_key(name="manager_id", to_=author, nullable=True),
    ),
)

content = factory.actions_tracked_table(
    name="content",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.integer(name="status", nullable=False),
        factory.string(name="caption", nullable=False),
        factory.text(name="preview", nullable=False),
        factory.text(name="body", nullable=False),
        factory.string(name="cover_url", nullable=True),
        factory.datetime(name="published_at", nullable=False),
        factory.foreign_key(name="author_id", to_=author, nullable=True)
    ),
)

evaluation = factory.actions_tracked_table(
    name="evaluations",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.integer(name="entity_kind", nullable=False),
        factory.uuid(name="entity_id", nullable=False),
        factory.uuid(name="author_id", nullable=False),
        factory.integer(name="value", nullable=True)
    ),
    constraints=(
        sqlalchemy.UniqueConstraint(
            "entity_id",
            "author_id",
            "deleted_at",
        ),
    ),
)

comment = factory.actions_tracked_table(
    name="comments",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.foreign_key(to_=content, name="content_id", nullable=False),
        factory.uuid(name="author_id", nullable=False),
        factory.text(name="body", nullable=True)
    ),
)

tag = factory.actions_tracked_table(
    name="tags",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.string(name="name", nullable=False)
    ),
)

group = factory.actions_tracked_table(
    name="groups",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.string(name="name", nullable=False)
    ),
)

tag_group = factory.table(
    name="tag_groups",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(autogenerate=True),
        factory.foreign_key(name="tag_id", to_=tag, nullable=False),
        factory.foreign_key(name="group_id", to_=group, nullable=False),
    ),
)

content_tag = factory.table(
    name="content_tags",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(autogenerate=True),
        factory.foreign_key(name="content_id", to_=content, nullable=False),
        factory.foreign_key(name="tag_id", to_=tag, nullable=False),
    ),
)

event = factory.actions_tracked_table(
    name="events",
    db_metadata=db_metadata,
    columns=(
        factory.uuid_primary_key(),
        factory.uuid(name="actor_id", nullable=False),
        factory.string(name="event_type", nullable=False),
        factory.jsonb(name="context", nullable=False)
    ),
)

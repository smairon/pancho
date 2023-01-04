import pydantic
import uuid
import datetime
import fastapi
from pancho.markup.schema import FilterSchema
from tacitus.definitions.contracts import Query, Node, Field


class MaterialFilterSchema(FilterSchema):
    id: str = fastapi.Query(None, value_type=uuid.UUID)
    caption: str = fastapi.Query(None, value_type=str)
    preview: str = fastapi.Query(None, value_type=str)
    author_id: str = fastapi.Query(None, value_type=uuid.UUID)
    published_at: str = fastapi.Query(None, value_type=datetime.datetime)
    author__first_name: str = fastapi.Query(None, value_type=str)


f = MaterialFilterSchema(
    **{
        'caption': '{ddd, sdfdsf}',
        'author_id': '!{51e47893-bd3a-4c68-b23b-d7d4b1b55694,fb741f53-3304-4b34-b138-372c0a907d4a}',
        'published_at': '[2022-01-01,2022-09-01]',
        'author__first_name': '~sergey'
    }
)
query = f.apply(
    query=Query(
        root_node=Node(
            relation="content",
            fields=[
                Field(name="caption")
            ]
        )
    )
)

k = query.root_node.filter
g = 3

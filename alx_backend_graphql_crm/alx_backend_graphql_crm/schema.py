import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# Define the root Query type
class Query(graphene.ObjectType):
    # 1. Define the 'hello' field
    # It will return a non-null String
    hello = graphene.String(default_value="Hello, GraphQL!")

class Query(CRMQuery, graphene.ObjectType):
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
# Note: For this simple case, the 'schema' variable is optional 
# as the URL config can take the Query class directly, but 
# defining it explicitly is often good practice:
schema = graphene.Schema(query=Query, mutation=Mutation)
from ingestion_engine.models.schema import Column, TableConfig

users = TableConfig(
    name="users",
    columns=[
        Column("id", "UInt64", "id"),
        Column("name", "String", "name"),
        Column("username", "String", "username"),
        Column("email", "String", "email"),
        Column("street", "String", "address.street"),
        Column("suite", "String", "address.suite"),
        Column("city", "String", "address.city"),
        Column("zipcode", "String", "address.zipcode"),
        Column("lat", "Float64", "address.geo.lat"),
        Column("lng", "Float64", "address.geo.lng"),
        Column("phone", "String", "phone"),
        Column("website", "String", "website"),
        Column("company_name", "String", "company.name"),
        Column("company_catch_phrase", "String", "company.catchPhrase"),
        Column("company_bs", "String", "company.bs"),
    ],
    order_by="id",
    source="json_placeholder__users"
)
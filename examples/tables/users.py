from ingestion_engine import Column, TableConfig

# The declared type must match the type the source actually returns: the
# framework normalizes the shape of a record, it does not cast its values.
# jsonplaceholder returns geo.lat and geo.lng as JSON strings, so they are
# declared as String and not as Float64.
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
        Column("lat", "String", "address.geo.lat"),
        Column("lng", "String", "address.geo.lng"),
        Column("phone", "String", "phone"),
        Column("website", "String", "website"),
        Column("company_name", "String", "company.name"),
        Column("company_catch_phrase", "String", "company.catchPhrase"),
        Column("company_bs", "String", "company.bs"),
    ],
    order_by="id",
    source="json_placeholder__users",
)

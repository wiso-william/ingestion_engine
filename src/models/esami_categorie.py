from .schema import Column, TableConfig

esami_categorie = TableConfig(
    name="esami_categorie",
    columns=[
        Column("id", "UInt64", "id"),
        Column("descrizione", "String", "descrizione"),
        Column("descrizione_breve", "String", "descrizione_breve"),
        Column("medical_area", "String", "medical_area"),
    ],
    order_by="id",
    source="json_placeholder__users"
)
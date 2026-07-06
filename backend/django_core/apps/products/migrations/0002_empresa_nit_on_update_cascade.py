from django.db import migrations


class Migration(migrations.Migration):
    """
    Change producto.empresa_nit FK from ON UPDATE NO ACTION to ON UPDATE CASCADE.
    This allows changing an empresa's NIT even when it has associated products.
    PostgreSQL will automatically propagate the new NIT to all producto rows.
    """

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    _constraint text;
                BEGIN
                    SELECT tc.constraint_name INTO _constraint
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_name = 'producto'
                      AND tc.constraint_type = 'FOREIGN KEY'
                      AND kcu.column_name = 'empresa_nit'
                    LIMIT 1;

                    IF _constraint IS NOT NULL THEN
                        EXECUTE 'ALTER TABLE producto DROP CONSTRAINT ' || quote_ident(_constraint);
                    END IF;
                END $$;

                ALTER TABLE producto
                    ADD CONSTRAINT producto_empresa_nit_fk
                    FOREIGN KEY (empresa_nit)
                    REFERENCES empresa(nit)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT;
            """,
            reverse_sql="""
                ALTER TABLE producto DROP CONSTRAINT IF EXISTS producto_empresa_nit_fk;
                ALTER TABLE producto
                    ADD CONSTRAINT producto_empresa_nit_fk_no_cascade
                    FOREIGN KEY (empresa_nit)
                    REFERENCES empresa(nit)
                    ON DELETE RESTRICT;
            """,
        ),
    ]

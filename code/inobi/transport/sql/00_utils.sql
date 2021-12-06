
create or replace function dump_transports_to_organization(organization_id int)
returns setof int as $$
begin
    return query
        insert into transport_organization_transports(organization, transport)
            select organization_id, id
                from transports
                where line_id in (
                    select line
                        from transport_organization_lines
                        where organization = organization_id
                )
            returning transport;
end;
$$ language plpgsql;

CREATE OR REPLACE VIEW buses(id, mac, line_id, number, type, plate, driver, device_phone)
    AS SELECT t.id, t.device_id, t.line_id, l.name, l.type, t.name, NULL::text, t.device_phone
        from transports as t
        LEFT JOIN routes as l ON t.line_id = l.id;


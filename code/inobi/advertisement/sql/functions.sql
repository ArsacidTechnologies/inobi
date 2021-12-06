


CREATE OR REPLACE FUNCTION calculate_distance(lat1 float, lon1 float, lat2 float, lon2 float)
RETURNS float AS
$$
select ACOS(SIN(RADIANS($1)) * SIN(RADIANS($3)) + COS(RADIANS($1)) * COS(RADIANS($3)) * COS(RADIANS($4) - RADIANS($2))) * 6371;
$$ LANGUAGE 'sql' IMMUTABLE;




create or replace function weighted_random(weight int) returns float as
$$
declare
    max_ float;
    rnd float;
begin
    max_ := 0.0;

    for counter in 1..weight loop

        rnd := random();

        if max_ < rnd then
            max_ := rnd;
        end if;

        counter := counter + 1;
    end loop;

    return max_;

end;
$$ LANGUAGE plpgsql;

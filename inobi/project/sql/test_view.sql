create or replace view test_db_initializer_view as
    select t1.* from test_db_initializer t1
        inner join test_db_initializer2 t2
            on t2.id = t1.id
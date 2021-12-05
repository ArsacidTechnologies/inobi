import psycopg2
from ...mobile_app.db.user import User



def get_drivers(organization, conn, asdict=False):
    sql = '''
        SELECT u.* FROM users u
        INNER JOIN transport_organization_drivers tod
            ON u.id = tod.user
        WHERE tod.organization = %s
    '''
    with conn.cursor() as cursor:
        cursor.execute(sql, (organization,))
        return [User.make(row)._asdict() if asdict else User.make_from_db_row(row)
                for row in cursor.fetchall()]



import psycopg2
from psycopg2 import extras
from datetime import datetime
import os

login_data = {
     'host': 'db',
     'database': 'eventdb',
     'user': 'postgres',
     'password': 'hiremepls'
}

create_tables_query = os.path.join(os.getcwd(), 'db', 'create_tables.sql')

insert_events_query = "INSERT INTO events (event_title, starting_time, venue_name, url, img_url) VALUES %s " \
                      "ON CONFLICT DO NOTHING"
insert_venues_query = "INSERT INTO venues (venue_name, venue_url, img_url, gmaps_url) VALUES %s " \
                      "ON CONFLICT DO NOTHING"
insert_composers_query = "INSERT INTO composers (composer_name, dob, dod) VALUES %s " \
                      "ON CONFLICT DO NOTHING"
insert_pieces_query = "INSERT INTO pieces (composer_name, title, event_title, event_starting_time) VALUES %s " \
                      "ON CONFLICT DO NOTHING"
insert_bookings_query = "INSERT INTO bookings (artist_name, event_title, event_starting_time) VALUES %s " \
                      "ON CONFLICT DO NOTHING"
insert_tickets_query = "INSERT INTO tickets (event_title, event_starting_time, price, available, " \
                       "first_check, last_check, first_sold_out_check) VALUES %s"


def create_db_access():
    con = psycopg2.connect(**login_data)
    cur = con.cursor()

    return con, cur


class DbAccessor:

    def __init__(self):
        self.con, self.cur = create_db_access()

    def get_db_access(self):
        return self.con, self.cur

    def close(self):
        self.con.close()
        self.cur.close()

    def reset_database(self):
        self.delete_all_tables()
        self.create_tables()
        print("Reset database")

    def delete_all_tables(self):
        self.cur.execute("drop schema public cascade; create schema public;")

    def create_tables(self):
        self.cur.execute(open(create_tables_query, "r").read())

    def insert_events(self, event_rows: list):
        extras.execute_values(self.cur, insert_events_query, event_rows)
        self.con.commit()

    def insert_venues(self, venue_rows: list):
        extras.execute_values(self.cur, insert_venues_query, venue_rows)
        self.con.commit()

    def insert_composers(self, composer_rows: list):
        extras.execute_values(self.cur, insert_composers_query, composer_rows)
        self.con.commit()

    def insert_pieces(self, pieces_rows: list):
        extras.execute_values(self.cur, insert_pieces_query, pieces_rows)
        self.con.commit()

    def insert_bookings(self, booking_rows: list):
        extras.execute_values(self.cur, insert_bookings_query, booking_rows)
        self.con.commit()

    def insert_tickets(self, ticket_rows: list):
        for ticket_row in ticket_rows:
            event_title, event_time, price, available = ticket_row
            first_sold_out_check = None
            self.cur.execute(f"SELECT * FROM tickets WHERE event_title = \'{event_title}\' "
                             f"AND event_starting_time = \'{event_time}\' AND price = \'{price}\'")
            existing_rows = self.cur.fetchall()
            if len(list(existing_rows)) == 0:
                first_check = datetime.now()

                if not available:
                    first_sold_out_check = datetime.now()

            else:
                existing_ticket = existing_rows[0]
                first_check = existing_ticket[4]

                last_availability = existing_ticket[3]

                if (not available) and last_availability:
                    first_sold_out_check = datetime.now()
                else:
                    first_sold_out_check = existing_ticket[6]

                self.cur.execute(f"DELETE FROM tickets WHERE event_title = \'{event_title}\' "
                                 f"AND event_starting_time = \'{event_time}\' AND price = \'{price}\'")

            last_check = datetime.now()

            ticket_row_extended = ticket_row + (first_check, last_check, first_sold_out_check)
            extras.execute_values(self.cur, insert_tickets_query, [ticket_row_extended])

        self.con.commit()

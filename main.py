import bs4
from bs4 import BeautifulSoup
import requests
import re
import db_utils
from datetime import datetime


main_page = 'https://www.lucernefestival.ch'
target_page = main_page + '/en/program/summer-festival-22'
current_year = 2022

# Reset database before loading; this is necessary, if you do not use docker and run this for the first time!
reset_database = False


# Parses the data and loads it into the database
def main():
    event_urls = get_event_urls()
    venue_rows = []
    event_rows = []
    pieces_rows = []
    composer_rows = []
    ticket_rows = []
    booking_rows = []

    # For every event, collect information and save in lists
    for event_url in event_urls:
        event_title, event_time, venue_name, img_url, venue_url,\
            composer_rows_event, pieces_rows_event, performers, tickets = get_event_details(event_url)

        print(f'Parsing event: {event_title}')
        event_rows.append((event_title, event_time, venue_name, event_url, img_url))
        venue_rows.append((venue_name, venue_url) + get_venue_details(venue_url))
        composer_rows += composer_rows_event
        pieces_rows += add_event_to_pieces_rows(pieces_rows_event, event_title, event_time)
        ticket_rows += [(event_title, event_time) + ticket for ticket in tickets]
        booking_rows += [(artist_name, event_title, event_time) for artist_name in performers]

    # Get rid of exact duplicates
    venue_rows = list(set(venue_rows))
    composer_rows = list(set(composer_rows))

    try:
        # Connect to the database
        db = db_utils.DbAccessor()

        # Possibly reset the database
        if reset_database:
            db.reset_database()

    except Exception:
        print("Failed to connect to the database.")


    try:
        # Insert data into the database and close the connection
        db.insert_events(event_rows)
        db.insert_venues(venue_rows)
        db.insert_composers(composer_rows)
        db.insert_pieces(pieces_rows)
        db.insert_tickets(ticket_rows)
        db.insert_bookings(booking_rows)
        db.close()
        print('Added to the database successfully')

    except Exception:
        print('Failed to insert data into the database.\nResetting the database might help.')


# Get the event URLs from the main page
def get_event_urls():
    doc = requests.get(target_page)
    soup = BeautifulSoup(doc.text, 'html.parser')
    return [main_page + x.find('a')['href'] for x in soup.find_all('li', {'class': 'event-item fl-clr yellow'})]


# Return details about the given event
def get_event_details(event_url):
    doc = requests.get(event_url)
    soup = BeautifulSoup(doc.text, 'html.parser')
    title = soup.find('h1').text

    date_time, venue_name = get_datetime_and_venue_name(soup)

    venue_url = get_venue_url(soup)
    composer_rows, pieces_rows = get_composer_and_pieces_rows(soup, title)
    performers = get_performers(soup)
    tickets = get_tickets(soup)
    img_url = get_img_url(soup)

    return title, date_time, venue_name, img_url, venue_url, composer_rows, pieces_rows, performers, tickets


# Get venue and date/time from event
def get_datetime_and_venue_name(event_soup):
    date_time_venue = list(event_soup.find("strong", string="Date and Venue").next_siblings)[-1]
    date, time, venue_name = " ".join(date_time_venue.split()).split(' | ')
    date_time = process_datetime(date, time)
    return date_time, venue_name


# Get available and sold out tickets
def get_tickets(event_soup):
    tickets = []

    # Past events
    past_event_status = event_soup.find('span', {'class': 'status past-event'})
    if past_event_status is not None:
        # print('Past event')
        return []

    # Free events
    free_event_status = event_soup.find('span', {'class': 'status free-entry'})
    if free_event_status is not None:
        return [(0, True)]

    price_tag = event_soup.find('div', {'class': 'prices'})
    if price_tag is not None:
        price_elements = price_tag.children

        for price_element in price_elements:

            if isinstance(price_element, bs4.element.Tag):
                if price_element['class'] == ['striked']:
                    tickets.append((int(price_element.text), False))
                else:
                    print(f'Unknown price element: {price_element.text}')
            else:
                tickets += [(int(price), True) for price in re.findall(r'\d+', price_element.text)]

        return tickets

    return []


# Find the venue URL on the event page
def get_venue_url(event_soup):
    venue_section = event_soup.find('section', {'id': 'venue'})
    venue_url = venue_section.find('a')['href']

    return main_page + venue_url


# Get the venue image and possibly Google Maps link
def get_venue_details(venue_url):
    doc = requests.get(venue_url)
    soup = BeautifulSoup(doc.text, 'html.parser')

    return get_img_url(soup), get_gmaps_url(soup)


# Get the venue image
def get_img_url(soup):
    img_container = soup.find('picture')

    try:
        image_url_ending = img_container.find('source')['srcset']
        if image_url_ending is not None:
            return main_page + image_url_ending

    except Exception:
        pass

    return None


# Get the Google Maps link of the venue
def get_gmaps_url(venue_soup):
    try:
        return venue_soup.find("a", href=lambda href: href and "/maps/" in href)['href']

    except Exception:
        return None


# Get a list of the performers at the event
def get_performers(event_soup):
    performers_list = event_soup.find('ul', {'class': 'performers-list'})

    if performers_list is None:
        return []

    performers_entries = performers_list.find_all('strong')

    return [clean_string(performer.text) for performer in performers_entries]


# Get lists of tuples for the composers and performed pieces
def get_composer_and_pieces_rows(event_soup, event_title):
    composer_rows = []
    pieces_rows = []
    found_composer = False

    program_items = event_soup.find_all('div', {'class': 'program-item'})
    if program_items:
        items = [program_item for program_item in program_items[1].parent.children]

        for item in items:
            if isinstance(item, bs4.element.Tag):
                item_class = item['class']

                if 'negative-margin' not in item_class:
                    composer_name_element = item.find('strong')
                    if composer_name_element is not None:
                        if composer_name_element.text != event_title:
                            name = composer_name_element.text
                            dob = process_dob(clean_string(composer_name_element.next_sibling.text))
                            if dob is None:
                                found_composer = False
                            else:
                                found_composer = True
                                composer_rows.append((name,) + dob)

                if found_composer:
                    pieces = item.find_all('em')
                    pieces_rows += [(name, piece.text) for piece in pieces]

        return composer_rows, pieces_rows

    return [], []


# Completes the pieces row for the database by adding event info to it
def add_event_to_pieces_rows(pieces_rows, event_title, event_timestamp):
    return [pieces_row + (event_title, event_timestamp) for pieces_row in pieces_rows]


# Converts the date information into a timestamp
def process_datetime(date: str, time: str):
    month = int(date[-3:-1])
    day = int(date[-6:-4])
    hour = int(time[:2])
    minutes = int(time[3:5])

    return datetime(current_year, month, day, hour, minutes)


# Processes birth and death years of composers
def process_dob(dob):
    years = [int(year) for year in re.findall(r'\d+', dob)]
    if len(years) == 1:
        return years[0], None
    elif len(years) == 2:
        return tuple(years)
    else:
        return None


# Cleans the names of performers and composers
def clean_string(string):
    string = string.replace('\n', '').replace('\t', '')
    if len(string) == 0:
        return string

    if string[-1] == ':':
        string = string[:-1]

    return string


if __name__ == "__main__":
    main()
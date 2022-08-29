CREATE TABLE events(
event_title VARCHAR,
starting_time TIMESTAMP,
venue_name VARCHAR,
url VARCHAR,
img_url VARCHAR,
PRIMARY KEY(event_title, starting_time));

CREATE TABLE venues(
venue_name VARCHAR PRIMARY KEY,
venue_url VARCHAR,
img_url VARCHAR,
gmaps_url VARCHAR);

CREATE TABLE composers(
composer_name VARCHAR PRIMARY KEY,
dob SMALLINT,
dod SMALLINT);

CREATE TABLE pieces(
composer_name VARCHAR,
title VARCHAR,
event_title VARCHAR,
event_starting_time TIMESTAMP);

CREATE TABLE bookings(
artist_name VARCHAR,
event_title VARCHAR,
event_starting_time TIMESTAMP);

CREATE TABLE tickets(
event_title VARCHAR,
event_starting_time TIMESTAMP,
price SMALLINT,
available BOOLEAN,
first_check TIMESTAMP,
last_check TIMESTAMP,
first_sold_out_check TIMESTAMP,
PRIMARY KEY(event_title, event_starting_time, price));
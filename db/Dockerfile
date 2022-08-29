FROM postgres:alpine
ENV POSTGRES_PASSWORD=hiremepls
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=eventdb
COPY create_tables.sql /docker-entrypoint-initdb.d/create_tables.sql
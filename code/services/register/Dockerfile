



FROM alpine:3.7
RUN set -ex && apk --no-cache add sudo curl postgresql-client
RUN set -ex && apk update && apk add bash && apk add tzdata
RUN set -ex && apk add ca-certificates && update-ca-certificates
ENV POSTGRES_PASSWORD=inobi
ENV POSTGRES_DB=inobi
ENV POSTGRES_USER=inobi
ENV POSTGRES_HOST=db
ENV INSERTION_SQL=init.sql
COPY register.sh .
COPY init.sql .
RUN chmod +x register.sh
CMD ["./register.sh"]
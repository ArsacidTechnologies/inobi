


FROM postgres:10-alpine
ENV SETUP=/var/lib/postgresql/setup
WORKDIR $SETUP
COPY init.sql $SETUP
RUN chmod 777 init.sql
COPY init.sql /docker-entrypoint-initdb.d
RUN set -ex && apk --no-cache add sudo curl
RUN set -ex && apk update && apk add bash && apk add tzdata
RUN set -ex && apk add ca-certificates && update-ca-certificates
ENV TZ=Asia/Tehran
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV LC_ALL=C.UTF-8
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
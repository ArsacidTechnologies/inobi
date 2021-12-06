
FROM openjdk:8-jre-alpine

ENV TRACCAR_VERSION 3.17

WORKDIR /opt/traccar

RUN set -ex && apk --no-cache add sudo
RUN set -ex && \
    apk update && apk add bash && \
    apk add --no-cache --no-progress wget && \
    wget -qO /tmp/traccar.zip https://github.com/traccar/traccar/releases/download/v$TRACCAR_VERSION/traccar-linux-$TRACCAR_VERSION.zip && \
    unzip -qo /tmp/traccar.zip -d /opt/traccar && chmod +x traccar.run && ./traccar.run && \
    rm /tmp/traccar.zip && \
    apk del wget

COPY traccar.xml conf

ENTRYPOINT ["java", "-Xms512m", "-Xmx512m", "-Djava.net.preferIPv4Stack=true"]

CMD ["-jar", "tracker-server.jar", "conf/traccar.xml"]

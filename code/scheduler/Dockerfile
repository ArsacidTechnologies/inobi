FROM python:alpine3.6

WORKDIR /opt/scheduler/

COPY requirements.txt ./

RUN apk --update add \
      build-base libffi-dev openssl-dev python3-dev \
      libffi openssl ca-certificates python3 tzdata

ENV TZ=Asia/Bishkek

RUN apk add \
      py3-lxml \
      py3-pillow

RUN pip3 install --upgrade python-dateutil \
                          arrow \
                          pytz \
                          zope.interface \
                          jinja2

RUN pip3 install --no-cache-dir -r requirements.txt

RUN apk del build-base libffi-dev openssl-dev python3-dev

RUN rm -rf /var/cache/apk/*

COPY . .

CMD [ "python", "./scheduler.py" ]

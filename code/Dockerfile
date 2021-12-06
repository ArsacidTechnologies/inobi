# pull official base image
FROM python:3.8.1-slim-buster as base_deploy

RUN groupadd -g 1000 aranobi && useradd -u 1000 -p "$(openssl passwd -1 "aranobi@4456%")" -ms /bin/bash -g aranobi aranobi && usermod -aG sudo aranobi

ENV APP_HOME=/opt/inobi/
WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Tehran
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV FLASK_APP='inobi:make_app()'


COPY requirements.txt $APP_HOME

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update && apt-get install -y --no-install-recommends gcc nano dialog postgresql-client apt-utils
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get install -y -q
RUN apt-get -y update && apt-get -y install build-essential \
    libffi-dev sudo python3-dev openssl libssl-dev python3 libpq-dev \
    python3-pip libjpeg-dev zlib1g-dev tzdata curl sox git

FROM base_deploy as python_deploy

RUN apt-get update && apt-get -y install python3-lxml \
          python3-lxml libxslt-dev ffmpeg
RUN pip3 install --upgrade Pillow python-dateutil \
                           arrow pytz \
                           pip \
                           zope.interface jinja2
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install --no-install-recommends -y cron netbase tcpdump

FROM python_deploy as final_deploy

COPY . $APP_HOME

RUN chown -R aranobi:aranobi $APP_HOME
USER aranobi
RUN crontab inobi.crontab
RUN chmod 777 $APP_HOME
RUN chmod 777 $APP_HOME/resources
RUN chmod +x runserver.py
USER root
RUN chown -R root:aranobi $APP_HOME/resources
RUN chmod +x init.sh

CMD ["./runserver.py", "--with-hooks"]
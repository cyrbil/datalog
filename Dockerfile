FROM python:3.7-alpine3.9

LABEL VERSION=1.0.0
ENV TERM xterm-256color

# configurable build arguments
ARG PUID=1000
ARG PGID=1000

# create unpriviledge user & group
RUN addgroup -g ${PGID} app \
 && adduser  -u ${PUID} -D -G app app

# use tini to allow proper signal handling (https://github.com/krallin/tini)
RUN apk add --no-cache tini

# install application dependencies
COPY requirements.txt /home/app/
RUN /usr/local/bin/pip install --upgrade --no-deps --require-hashes -r /home/app/requirements.txt

# drop priviledges & set home
USER app
WORKDIR /home/app

# deploy application
COPY datalog_http_monitoring /home/app/datalog_http_monitoring

# run application
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/python", "-m", "datalog_http_monitoring"]

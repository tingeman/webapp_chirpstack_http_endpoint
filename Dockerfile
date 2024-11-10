# Using python
FROM python:3.12-slim

ENV DASH_DEBUG_MODE False

# Create the web user with UID 30000
RUN adduser --disabled-password --no-create-home --uid 30000 web

# Install the GitHub Actions Runner 
RUN apt-get update \
    && apt-get install -y sudo curl nano wget unzip git \
    && usermod -aG sudo web \
    && echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/www/app/data \
    && chown -R web:web /var/www/app \
    && chmod -R 755 /var/www/app

WORKDIR /var/www/app

COPY ./app/requirements.txt ./requirements.txt
RUN set -ex && \
    python -m pip install --no-cache-dir -r ./requirements.txt

USER web
COPY --chown=web:web ./app /var/www/app/


EXPOSE 8050
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--log-level", "debug", "app:app"]
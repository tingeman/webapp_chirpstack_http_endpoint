# Using python
FROM python:3.12-slim

ENV DASH_DEBUG_MODE False

# Create the web user with UID 30000
RUN adduser --disabled-password --no-create-home --uid 30000 web

# Install the GitHub Actions Runner 
RUN apt-get update --no-cache && apt-get install -y sudo curl nano wget unzip git \
    && usermod -aG sudo web \
    && echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/app

COPY ./app/requirements.txt ./requirements.txt
RUN set -ex && \
    python -m pip install --no-cache-dir -r ./requirements.txt

USER web
COPY --chown=web:web ./app /var/www/app/

EXPOSE 8050
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--reload", "app:app"]
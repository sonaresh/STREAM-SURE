FROM python:3.13-slim

ARG APP_UID=10001
ARG APP_GID=10001

WORKDIR /app

# Create an explicit non-root runtime identity so Kubernetes runAsNonRoot is enforceable.
RUN groupadd --gid ${APP_GID} streamsure \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --create-home --shell /usr/sbin/nologin streamsure \
    && mkdir -p /data \
    && chown -R ${APP_UID}:${APP_GID} /app /data

COPY --chown=${APP_UID}:${APP_GID} . /app
RUN pip install --no-cache-dir .

USER ${APP_UID}:${APP_GID}

EXPOSE 8080
CMD ["streamsure","serve","--host","0.0.0.0","--port","8080","--db","/data/streamsure.db"]

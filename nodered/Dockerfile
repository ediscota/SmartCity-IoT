FROM nodered/node-red:4.0

USER root

# Utility opzionali
RUN apk add --no-cache jq

# Torniamo all'utente node-red
USER node-red

# Lavoriamo nella userDir reale di Node-RED
WORKDIR /data

# Installiamo i nodi dentro /data
RUN npm install \
    node-red-dashboard \
    node-red-contrib-influxdb \
    node-red-contrib-telegrambot

# Avvio standard di Node-RED sulla userDir /data
ENTRYPOINT ["/bin/sh", "-c", "exec npm start --cache /data/.npm -- --userDir /data"]

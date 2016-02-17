This tools is use MX record's IP and GeoIP database to determine use which regional relay server to delivery email to destination.

Postfix use TCP transport map connect to this program.

Postfix config:
`transport_maps = tcp:[127.0.0.1]:2527`
# frozone
A set of tools to integrate Keemple thermostats with MQTT

## lucius

This one reads the state of the thermostats and publishes to data to MQTT

## honey

This one subscribes to the `set` topic and executes the operations necessary to
set the desired temperature.

## frozone

A Discord bot serving as UI for the above.

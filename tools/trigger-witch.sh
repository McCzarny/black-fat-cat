#!/bin/bash

GPIO=247

echo "$GPIO" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio$GPIO/direction

echo "Turn on witch"
echo "1" > /sys/class/gpio/gpio$GPIO/value  # Turn ON
sleep 30
echo "Make witch sleep"
echo "0" > /sys/class/gpio/gpio$GPIO/value  # Turn OFF

# Cleanup
echo "$GPIO" > /sys/class/gpio/unexport
# Quintuple E

2023/24 End of Year Project
==============================

This repository contains the smart grid & energy management project produced as part of the EIE 2nd Year End of Year coursework at Imperial College London completed in Spring 2024 by John Yeo, Ajith Kurian, Intishar Misbahul, Jay Mistry, Vishesh Mongia and myself (Noam Weitzman). 

Overview
================

This repo presents the design and implementation of an energy management system to optimise energy supply within a smart grid context. The project integrates a photovoltaic (PV) array for renewable energy generation,
supercapacitors for energy storage, an external grid connection, and various LED loads. The primary goal is to efficiently manage energy usage while minimising reliance on the external grid, driven by demands provided by a third-party web server. Key components include maximum power point tracking (MPPT) algorithms for the PV array, cost-minimising algorithms utilising historical data, reinforcement learning for energy demand
prediction, and multiple control systems to ensure proper functionality. Communication within the system is facilitated via MQTT, data is stored using a NoSQL database, and a user interface (UI) provides real-time and historical views of power flows. The project demonstrates effective energy management and offers a scalable
model for integrating renewable energy sources into existing infrastructure, enhancing overall energy efficiency.



File Strucuture
================

## Software Folder

- broker/mosquitto.conf - contains the configuration file for the mosquitto broker.

- dashboard - contains the code for the UI

    - app - contains the code for each page
    
    - app/actions.ts - contains functions for the Next.js server actions

    - components - custom UI elements used throughout the dashboard

    - helper - contains code used to get and process graph data and data from the MQTT broker

- pico_simulation - MQTT client used to test the UI and backend service

- server/main.py - runs the algorithm for the backend service

- server/external - contains optimisations to fetch data and sync with the external web server

- server/optimisation - contains files to run the optimisation algorithm

- trend_prediction - contains notebooks on tests we ran with the data generated from the external web server

- trend_prediction/price_prediction - contains models built to predict the buy price from the external web server

## Hardware

- Each hardware subsystem has its own folder with the code running on the Pico W

- Server Comms - contains code to run on all picos:

    - Server Comms/mqtt_client.py - to connect, receive and send messages with the MQTT broker
    
    - Server Comms/wifi.py - to connect the Pico W to the internet

## Videos

- [Grid UI Video](https://youtu.be/6DRRmUU25tM?si=uK3EfAKqUYMd-oMA) - Explanation of the grid UI used in the dashboard.

- [MPPT Explanation Video](https://youtu.be/Mqih-1-pDE8?si=VUjKUSX0d-B3s6bj) - Explanation of the MPPT used in demo.

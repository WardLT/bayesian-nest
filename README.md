# Bayesian Nest

The goal of this repository is to create a statistically-robust model for my home's HVAC system using Bayesian modeling.

The key features are...
- pulling a temperature and operation history of the home from the Google Nest API
- cross-referencing the home temperature with weather reports
- fitting different models for the home's temperature state using Bayesian methods

When complete, the models will allow you to determine optimal policies for the system 
depending on whether forecasts and assessing whether the variation of the observed performance
are within expected bounds.

## Installation, Setup, and Configuration

The required packages for this package are in the `requirements.txt` file. 
I recommend that you install the package into a virtual environment using Anaconda
(there is an Anaconda environment provided) or Python's virtual environment.

### Security Tokens

#### Gaining Access to Nest Data

Once installed, you must register with Google to be able to access your Nest's data via an API.
Follow the instructions on the ["Device Access" Tutorial](https://developers.google.com/nest/device-access/registration).
During this procedure, you will download two different JSON files:

1. *Project ID*: You will create a Device Access project ID in the first step. Change the project ID in
   [bayesest/thermo.py](./bayesnest/thermostat.py) to your project ID. 
2. *OAuth 2.0 Client Information*. You will download a JSON file when 
   configuring [Google Cloud Platform during Step 1](https://developers.google.com/nest/device-access/get-started#set_up_google_cloud_platform).
   Save this file to `bayesnest/creds/google-sdm-service.json`.
3. *Account Authorization Tokens*. You will download a set of keys via curl after authorizing your Google API Client
    to access your Google account. Save this JSON file to `./bayesnest/creds/google-sdm-user.json`.

> **NOTE**: Do not share either of these JSON files with anyone!

#### Weather data

Sign up for an account with [OpenWeatherMap](https://openweathermap.org/), validate your email address, 
and then paste the API key into [`weather.py`](./bayesnest/weather.py).

> **NOTE**: You do not need to register for the OneAPI/v3 service. Our app uses v2.5 

### Launching the service

Active the environment and then call `bayesnest`

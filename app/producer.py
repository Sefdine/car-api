# Import necessary packages
from faker import Faker
import random
import json
import sys
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import logging
import time
from datetime import datetime
from decimal import Decimal

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
    
# Set up logging
logging.basicConfig(level=logging.INFO)

# Define the topic name and the bootstrap server
TOPIC = 'cars'
SERVER_NAME = 'localhost:9092'

# Initialize kafka producer
print('Connecting to Kafka')
try:
    producer = KafkaProducer(bootstrap_servers=SERVER_NAME, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    print('Connection done !')
except NoBrokersAvailable as ne:
    logging.error('No brokers available: %s', ne)
    sys.exit(1)

# Create Faker instance
fake = Faker()

count = 1

vin_list = [fake.uuid4() for _ in range(1000)]


while True:

    # Introduce duplicates
    if count % 10 == 0:
        duplicate_vin = random.choice(vin_list)
    else:
        duplicate_vin = None

    vin = duplicate_vin if duplicate_vin else fake.uuid4(),
    # Location Data
    latitude = fake.latitude()
    longitude = fake.longitude()
    altitude = random.uniform(0, 500)  # Random altitude between 0 and 500 meters

    # Vehicle Telemetry
    speed = random.uniform(0, 120)  # Random speed between 0 and 120 km/h
    acceleration = random.uniform(-5, 5)  # Random acceleration between -5 and 5 m/s^2
    braking_intensity = random.uniform(0, 1)  # Random braking intensity between 0 and 1
    fuel_consumption = random.uniform(5, 15)  # Random fuel consumption between 5 and 15 km/l

    # Engine Diagnostics
    engine_temperature = random.uniform(80, 100)  # Random engine temperature between 80 and 100 degrees Celsius
    rpm = random.uniform(1000, 6000)  # Random RPM between 1000 and 6000

    # Safety Features
    airbag_deployed = random.choice([True, False])
    abs_activated = random.choice([True, False])

    # Environmental Data
    ambient_temperature = random.uniform(-10, 40)  # Random temperature between -10 and 40 degrees Celsius
    humidity = random.uniform(0, 100)  # Random humidity between 0 and 100%
    air_quality = random.uniform(0, 1)  # Random air quality index between 0 and 1

    # Entertainment and Infotainment
    media_usage = fake.random_int(0, 100)  # Random media usage percentage
    connectivity_status = random.choice(['Connected', 'Disconnected'])

    # Maintenance Data
    tire_pressure = random.uniform(28, 35)  # Random tire pressure between 28 and 35 psi
    battery_status = random.choice(['Good', 'Low', 'Critical'])

    # Connectivity and Communication
    network_strength = fake.random_int(1, 5)  # Random network strength between 1 and 5
    data_usage = fake.random_int(0, 100)  # Random data usage percentage

    # Security and Anti-Theft
    gps_tracking = fake.random_int(0, 1)  # Random GPS tracking status (0 or 1)
    door_lock_status = random.choice(['Locked', 'Unlocked'])

    # Driver Behavior
    steering_pattern = random.choice(['Aggressive', 'Normal', 'Cautious'])
    lane_departure_warning = random.choice([True, False])

    # Usage and Performance Metrics
    total_mileage = fake.random_int(1000, 50000)  # Random total mileage between 1000 and 50000 km
    time_in_operation = fake.random_int(1, 365)  # Random time in operation between 1 and 365 days

    # Generate a timestamp within the last year for date-related attributes
    timestamp = fake.date_time_between(start_date='-1y', end_date='now')

    fake_data = json.dumps({
        'Timestamp': timestamp,
        'VIN': vin,
        'Latitude': latitude,
        'Longitude': longitude,
        'Altitude': altitude,
        'Speed': speed,
        'Acceleration': acceleration,
        'Braking Intensity': braking_intensity,
        'Fuel Consumption': fuel_consumption,
        'Engine Temperature': engine_temperature,
        'RPM': rpm,
        'Airbag Deployed': airbag_deployed,
        'ABS Activated': abs_activated,
        'Ambient Temperature': ambient_temperature,
        'Humidity': humidity,
        'Air Quality': air_quality,
        'Media Usage': media_usage,
        'Connectivity Status': connectivity_status,
        'Tire Pressure': tire_pressure,
        'Battery Status': battery_status,
        'Network Strength': network_strength,
        'Data Usage': data_usage,
        'GPS Tracking': gps_tracking,
        'Door Lock Status': door_lock_status,
        'Steering Pattern': steering_pattern,
        'Lane Departure Warning': lane_departure_warning,
        'Total Mileage': total_mileage,
        'Time in Operation': time_in_operation
    }, cls=CustomJSONEncoder)

    try:
        producer.send(TOPIC, value=fake_data)
        producer.flush()

        logging.info(f"INFO: Fake data {count} sent successfully!")
        count += 1
        time.sleep(1)
    except NoBrokersAvailable as ne:
        logging.error('No brokers available: %s', ne)
        break
    except Exception as e:
        logging.error('Error: %s', e)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Closing Kafka producer connection...")
        producer.close()
        print("Kafka producer connection closed.")
        sys.exit(0)

producer.close()
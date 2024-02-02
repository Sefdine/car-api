from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, BooleanType
from pyspark.sql.functions import from_json
from elasticsearch import Elasticsearch
from pymongo import MongoClient
import concurrent.futures
import json
import logging
import sys

# Define a topic name
TOPIC_NAME = 'cars'

print('Connecting to Kafka: ')
try:
    consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers='localhost:9092')
    print('Connection done !')
except NoBrokersAvailable as ne:
    logging.error('No brokers available: %s', ne)
    sys.exit(1)

# Create a Spark session
spark = SparkSession.builder \
    .appName("cars_api") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0") \
    .getOrCreate()

# schema to map
schema = StructType([
    StructField('Timestamp', StringType(), True),
    StructField('VIN', StringType(), True),
    StructField('Latitude', FloatType(), True),
    StructField('Longitude', FloatType(), True),
    StructField('Altitude', FloatType(), True),
    StructField('Speed', FloatType(), True),
    StructField('Acceleration', FloatType(), True),
    StructField('Braking Intensity', FloatType(), True),
    StructField('Fuel Consumption', FloatType(), True),
    StructField('Engine Temperature', FloatType(), True),
    StructField('RPM', FloatType(), True),
    StructField('Airbag Deployed', BooleanType(), True),
    StructField('ABS Activated', BooleanType(), True),
    StructField('Ambient Temperature', FloatType(), True),
    StructField('Humidity', FloatType(), True),
    StructField('Air Quality', FloatType(), True),
    StructField('Media Usage', StringType(), True),
    StructField('Connectivity Status', StringType(), True),
    StructField('Tire Pressure', FloatType(), True),
    StructField('Battery Status', StringType(), True),
    StructField('Network Strength', FloatType(), True),
    StructField('Data Usage', FloatType(), True),
    StructField('GPS Tracking', BooleanType(), True),
    StructField('Door Lock Status', BooleanType(), True),
    StructField('Steering Pattern', StringType(), True),
    StructField('Lane Departure Warning', BooleanType(), True),
    StructField('Total Mileage', FloatType(), True),
    StructField('Time in Operation', FloatType(), True)
])

# Connect to Elasticsearch
es = Elasticsearch(['localhost:9200'])

# Define the index
index_name = 'cars'

# Connect to MongoDB
mongo_client = MongoClient('localhost', 27017)
mongo_db = mongo_client['cars_db']
mongo_collection = mongo_db['cars_collection']

# Function to handle insertion into Elasticsearch
def index_into_elasticsearch(doc):
    try:
        es.index(index=index_name, document=doc)
        print("Data indexed into Elasticsearch successfully.")
    except Exception as e:
        print('Error indexing into Elasticsearch: ', e)

# Function to handle insertion into MongoDB
def insert_into_mongodb(doc):
    try:
        mongo_collection.insert_one(doc)
        print("Data inserted into MongoDB successfully.")
    except Exception as e:
        print('Error inserting into MongoDB: ', e)

cars_count = 0
for message in consumer:
    # Convert the bytes object to a string
    message_str = message.value.decode('utf-8')

    json_dict = json.loads(message_str)

    # Create a DataFrame with a single row
    df = spark.createDataFrame([json_dict], StringType())

    # Directly select the columns from the JSON string
    parsed_df = df.select(from_json("value", schema).alias("data")).select("data.*")

    # Show the parsed DataFrame
    parsed_df.show(truncate=False)

    try:
        # Convert the Spark DataFrame to a Pandas DataFrame
        pd_df = parsed_df.toPandas()

        # Convert the Pandas DataFrame to a dictionary
        doc = pd_df.to_dict(orient='records')[0]

        # Perform parallel insertion using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks for insertion into Elasticsearch and MongoDB
            elasticsearch_future = executor.submit(index_into_elasticsearch, doc.copy())
            mongodb_future = executor.submit(insert_into_mongodb, doc.copy())

            # Wait for both tasks to complete
            concurrent.futures.wait([elasticsearch_future, mongodb_future])

        print(f"Car {cars_count} processed!")
        cars_count += 1
    except Exception as e:
        print('Error: ', e)
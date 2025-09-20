from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, InvalidURI
from dotenv import load_dotenv
import os

def database_connection(database: str, collection: str):
    """
    Returns a connection to the dev database for a specific database and collection.

    Args:
        database: The name of the database you want to use.
        collection: The name of the collection you want to use.

    Returns:
        Connection object to database.

    Raises:
        ConnectionFailure: Could not connect to MongoDB.
        ServerSelectionTimeoutError: No suitable server found.
        InvalidURI: MongoDB URI is invalid.
        Exception: Unexpected error.
    """
    try:
        load_dotenv('.env.dev')

        # MongoDB connection
        user = os.getenv('MONGO_USER')
        passwd = os.getenv('MONGO_PASS')
        server = os.getenv('MONGO_IP')

        db_client = MongoClient(f"mongodb://{user}:{passwd}@{server}:27017/")
        db = db_client[database]
        db_collection = db[collection]
        
        print("Successfully connected to MongoDB!")
        return db_collection
    
    except ConnectionFailure as e:
        print(f"ConnectionFailure: Could not connect to MongoDB: {e}")
        return None
    except ServerSelectionTimeoutError as e:
        print(f"ServerSelectionTimeoutError: No suitable server found: {e}")
        return None
    except InvalidURI as e:
        print(f"InvalidURI: The provided MongoDB URI is invalid: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during connection: {e}")
        return None
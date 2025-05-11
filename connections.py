import psycopg2
import redis
from elasticsearch import Elasticsearch
import logging
from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER,
    POSTGRES_PASSWORD, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD,
    ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
)

logger = logging.getLogger(__name__)


# PostgreSQL connection
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        if conn:
            conn.close()
        return None


# Redis connection
def get_redis_connection():
    try:
        if REDIS_PASSWORD:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
        else:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
        return r
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        return None


# Elasticsearch connection
def get_elasticsearch_connection():
    try:
        connection_url = (
            f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"
        )
        logger.info(
            f"Attempting to connect to Elasticsearch at: {connection_url}"
        )
        # es = Elasticsearch(
        #     connection_url,
        #     basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
        #     verify_certs=False,
        #     request_timeout=30,
        #     retry_on_timeout=True,
        #     max_retries=3,
        #     api_key=None,
        # )
        es = Elasticsearch(
            hosts=[{
                "host": ELASTICSEARCH_HOST,
                "port": ELASTICSEARCH_PORT,
                "scheme": "http",
            }],
            basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
        )
        # Test the connection immediately
        if es.ping():
            logger.info("Successfully connected to Elasticsearch")
        else:
            logger.error("Failed to ping Elasticsearch")

        return es
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")
        return None


# Health check function
async def check_connections():
    results = {
        "postgres": False,
        "redis": False,
        "elasticsearch": False
    }

    # Check PostgreSQL
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            results["postgres"] = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")

    # Check Redis
    try:
        r = get_redis_connection()
        if r and r.ping():
            results["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    # Check Elasticsearch
    try:
        es = get_elasticsearch_connection()
        if es:
            try:
                # Try to get cluster info instead of health
                info = es.info()
                logger.info(f"Elasticsearch info: {info}")
                results["elasticsearch"] = True
            except Exception as e:
                logger.error(f"Elasticsearch health check failed: {str(e)}")
    except Exception as e:
        logger.error(f"Elasticsearch connection failed: {str(e)}")

    return results, all(results.values())

"""
Database configuration module for City Rides Analytics.

This module provides database connection configuration and management
using environment variables loaded from .env file.
"""

import os

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration class for PostgreSQL connection with connection pooling."""

    _connection_pool = None

    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "city_rides_db")
        self.user = os.getenv("DB_USER", "rides_user")
        self.password = os.getenv("DB_PASSWORD", "")

        # Initialize connection pool if not already created
        if DatabaseConfig._connection_pool is None:
            self._init_connection_pool()

    def _init_connection_pool(self):
        """
        Initialize the connection pool.
        Uses SimpleConnectionPool for single-threaded applications.
        """
        try:
            DatabaseConfig._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,  # Minimum connections to maintain
                maxconn=20,  # Maximum concurrent connections
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print(f"Connection pool initialized: 2-20 connections to {self.database}")
        except Exception as e:
            print(f"Error initializing connection pool: {e}")
            raise

    def get_connection_string(self):
        """
        Get PostgreSQL connection string.

        Returns:
            str: PostgreSQL connection string in format:
                postgresql://user:password@host:port/database
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_engine(self):
        """
        Create and return SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy engine instance
        """
        return create_engine(self.get_connection_string())

    def get_session(self):
        """
        Create and return SQLAlchemy session.

        Returns:
            Session: SQLAlchemy session instance
        """
        engine = self.get_engine()
        Session = sessionmaker(bind=engine)
        return Session()

    def get_connection(self):
        """
        Get a connection from the pool.

        Returns:
            connection: psycopg2 connection instance from pool
        """
        try:
            return DatabaseConfig._connection_pool.getconn()
        except Exception as e:
            print(f"Error getting connection from pool: {e}")
            raise

    def return_connection(self, conn):
        """
        Return a connection to the pool.

        Args:
            conn: psycopg2 connection to return to pool
        """
        try:
            DatabaseConfig._connection_pool.putconn(conn)
        except Exception as e:
            print(f"Error returning connection to pool: {e}")
            raise

    def close_all_connections(self):
        """
        Close all connections in the pool.
        Should be called on application shutdown.
        """
        if DatabaseConfig._connection_pool:
            DatabaseConfig._connection_pool.closeall()
            print("All database connections closed")


if __name__ == "__main__":
    # Test configuration
    config = DatabaseConfig()
    print(f"Database: {config.database}")
    print(f"Host: {config.host}")
    print(f"Port: {config.port}")
    print(f"User: {config.user}")
    print("Connection string generated successfully!")

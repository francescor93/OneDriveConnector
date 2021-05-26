import logging


class ConnectorException(Exception):
    def __init__(self, message):
        exception_logger = logging.getLogger(
            'connector_logger.connectorexception')
        exception_logger.error(message)
        super().__init__(message)

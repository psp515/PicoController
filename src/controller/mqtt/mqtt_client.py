from configuration.features.mqtt_options import MqttOptions
from umqtt.simple import MQTTClient

from logging.logger import Logger


class MqttClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MqttClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.logger = Logger()
            self.initialized = True
            self._options = MqttOptions()
            self._callbacks = {}

            if self._options.empty():
                raise ValueError("MQTT options are not set.")

            self._client = MQTTClient(
                client_id=self._options.client,
                server=self._options.url,
                port=self._options.port,
                user=self._options.username,
                password=self._options.password,
                keepalive=self._options.keep_alive,
                ssl=True,
                ssl_params={"server_hostname": self._options.url})

            self._client.set_callback(self._callback)

    def _callback(self, topic, message):
        try:
            topic = topic.decode("utf-8")
            data = message.decode("utf-8")

            self.logger.info(f"Topic: '{topic}'. ")
            self.logger.debug(f"Payload: {data}. ")

            if topic not in self._callbacks:
                self.logger.warning(f"{topic} not found in topics. Ignoring message")
                return

            function = self._callbacks[topic]
            function(data)

        except Exception as e:
            self.logger.error(f"Error when processing topic: {topic}.")
            self.logger.debug(f"Error: {e}")

    def connect(self):
        self._client.connect()
        self.logger.info("Connected to MQTT broker.")

    def reconnect(self):
        # Clean session is set to False to keep the subscriptions
        self.logger.debug("Trying to reconnect to MQTT broker.")
        self.connect(clean_session=False)

    def is_connected(self):
        return self._client.is_connected()

    def publish(self, topic: str, message: str):
        encoded_topic = topic.encode('utf-8')
        encoded_message = message.encode('utf-8')
        self._client.publish(encoded_topic, encoded_message)
        self.logger.debug(f"Published on topic: {topic} message: {message}")

    def subscribe(self, topic: str, callback):
        self._client.subscribe(topic)
        self._callbacks[topic] = callback

    def get_message(self):
        return self._client.wait_msg()

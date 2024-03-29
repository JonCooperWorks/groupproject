import base64
import copy
import json
import sys
from keen import persistence_strategies, exceptions
from keen.api import KeenApi
from keen.persistence_strategies import BasePersistenceStrategy

__author__ = 'dkador'


class Event(object):
    """
    An event in Keen.
    """

    def __init__(self, project_id, event_collection, event_body,
                 timestamp=None):
        """ Initializes a new Event.

        :param project_id: the Keen project ID to insert the event to
        :param event_collection: the Keen collection name to insert the event to
        :param event_body: a dict that contains the body of the event to insert
        :param timestamp: optional, specify a datetime to override the
        timestamp associated with the event in Keen
        """
        super(Event, self).__init__()
        self.project_id = project_id
        self.event_collection = event_collection
        self.event_body = event_body
        self.timestamp = timestamp

    def to_json(self):
        """ Serializes the event to JSON.

        :returns: a string
        """
        event_as_dict = copy.deepcopy(self.event_body)
        if self.timestamp:
            event_as_dict["keen"] = {"timestamp": self.timestamp.isoformat()}
        return json.dumps(event_as_dict)


class KeenClient(object):
    """ The Keen Client is the main object to use to interface with Keen. It
    requires a project ID and one or both of write_key and read_key.

    Optionally, you can also specify a persistence strategy to elect how
    events are handled when they're added. The default strategy is to send
    the event directly to Keen, in-line. This may not always be the best
    idea, though, so we support other strategies (such as persisting
    to a local Redis queue for later processing).
    """

    def __init__(self, project_id, write_key=None, read_key=None,
                 persistence_strategy=None):
        """ Initializes a KeenClient object.

        :param project_id: the Keen IO project ID
        :param write_key: a Keen IO Scoped Key for Writes
        :param read_key: a Keen IO Scoped Key for Reads
        :param persistence_strategy: optional, the strategy to use to persist
        the event
        """
        super(KeenClient, self).__init__()

        # do some validation
        if not project_id or not isinstance(project_id, str):
            raise exceptions.InvalidProjectIdError(project_id)

        # Set up an api client to be used for querying and optionally passed
        # into a default persistence strategy.
        self.api = KeenApi(project_id, write_key=write_key, read_key=read_key)

        if persistence_strategy:
            # validate the given persistence strategy
            if not isinstance(persistence_strategy, BasePersistenceStrategy):
                raise exceptions.InvalidPersistenceStrategyError()
        if not persistence_strategy:
            # setup a default persistence strategy
            persistence_strategy = persistence_strategies \
                .DirectPersistenceStrategy(self.api)

        self.project_id = project_id
        self.persistence_strategy = persistence_strategy

    def add_event(self, event_collection, event_body, timestamp=None):
        """ Adds an event.

        Depending on the persistence strategy of the client,
        this will either result in the event being uploaded to Keen
        immediately or will result in saving the event to some local cache.

        :param event_collection: the name of the collection to insert the
        event to
        :param event_body: dict, the body of the event to insert the event to
        :param timestamp: datetime, optional, the timestamp of the event
        """
        event = Event(self.project_id, event_collection, event_body,
                      timestamp=timestamp)
        self.persistence_strategy.persist(event)

    def add_events(self, events):
        """ Adds a batch of events.

        Depending on the persistence strategy of the client,
        this will either result in the event being uploaded to Keen
        immediately or will result in saving the event to some local cache.

        :param events: dictionary of events
        """
        self.persistence_strategy.batch_persist(events)

    def generate_image_beacon(self, event_collection, event_body, timestamp=None):
        """ Generates an image beacon URL.

        :param event_collection: the name of the collection to insert the
        event to
        :param event_body: dict, the body of the event to insert the event to
        :param timestamp: datetime, optional, the timestamp of the event
        """
        event = Event(self.project_id, event_collection, event_body,
                      timestamp=timestamp)
        event_json = event.to_json()
        return "{0}/{1}/projects/{2}/events/{3}?api_key={4}&data={5}".format(
            self.api.base_url, self.api.api_version, self.project_id, self._url_escape(event_collection),
            self.api.write_key.decode(sys.getdefaultencoding()), self._base64_encode(event_json)
        )

    def _base64_encode(self, string_to_encode):
        """ Base64 encodes a string, with either Python 2 or 3.

        :param string_to_encode: the string to encode
        """
        try:
            # python 2
            return base64.b64encode(string_to_encode)
        except TypeError:
            # python 3
            encoding = sys.getdefaultencoding()
            base64_bytes = base64.b64encode(bytes(string_to_encode, encoding))
            return base64_bytes.decode(encoding)

    def _url_escape(self, url):
        try:
            import urllib
            return urllib.quote(url)
        except AttributeError:
            import urllib.parse
            return urllib.parse.quote(url)

    def count(self, event_collection, timeframe=None, timezone=None, interval=None, filters=None, group_by=None):
        """ Performs a count query

        Counts the number of events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by)
        return self.api.query("count", params)

    def sum(self, event_collection, target_property, timeframe=None, timezone=None, interval=None, filters=None,
            group_by=None):
        """ Performs a sum query

        Adds the values of a target property for events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param target_property: string, the name of the event property you would like use
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by, target_property=target_property)
        return self.api.query("sum", params)

    def minimum(self, event_collection, target_property, timeframe=None, timezone=None, interval=None, filters=None,
                group_by=None):
        """ Performs a minimum query

        Finds the minimum value of a target property for events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param target_property: string, the name of the event property you would like use
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by, target_property=target_property)
        return self.api.query("minimum", params)

    def maximum(self, event_collection, target_property, timeframe=None, timezone=None, interval=None, filters=None,
                group_by=None):
        """ Performs a maximum query

        Finds the maximum value of a target property for events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param target_property: string, the name of the event property you would like use
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by, target_property=target_property)
        return self.api.query("maximum", params)

    def average(self, event_collection, target_property, timeframe=None, timezone=None, interval=None, filters=None,
                group_by=None):
        """ Performs a average query

        Finds the average of a target property for events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param target_property: string, the name of the event property you would like use
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by, target_property=target_property)
        return self.api.query("average", params)

    def count_unique(self, event_collection, target_property, timeframe=None, timezone=None, interval=None,
                     filters=None, group_by=None):
        """ Performs a count unique query

        Counts the unique values of a target property for events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param target_property: string, the name of the event property you would like use
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by, target_property=target_property)
        return self.api.query("count_unique", params)

    def select_unique(self, event_collection, target_property, timeframe=None, timezone=None, interval=None,
                      filters=None, group_by=None):
        """ Performs a select unique query

        Returns an array of the unique values of a target property for events that meet the given criteria.

        :param event_collection: string, the name of the collection to query
        :param target_property: string, the name of the event property you would like use
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param interval: string, the time interval used for measuring data over
        time example: "daily"
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 interval=interval, filters=filters, group_by=group_by, target_property=target_property)
        return self.api.query("select_unique", params)

    def extraction(self, event_collection, timeframe=None, timezone=None, filters=None, latest=None, email=None):
        """ Performs a data extraction

        Returns either a JSON object of events or a response
         indicating an email will be sent to you with data.

        :param event_collection: string, the name of the collection to query
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param latest: int, the number of most recent records you'd like to return
        :param email: string, optional string containing an email address to email results to

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 filters=filters, latest=latest, email=email)
        return self.api.query("extraction", params)

    def funnel(self, steps, timeframe=None, timezone=None):
        """ Performs a Funnel query

        Returns an object containing the results for each step of the funnel.

        :param steps: array of dictionaries, one for each step. example:
        [{"event_collection":"signup","actor_property":"user.id"},
        {"event_collection":"purchase","actor_property:"user.id"}]
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds

        """
        params = self.get_params(steps=steps, timeframe=timeframe, timezone=timezone)
        return self.api.query("funnel", params)

    def multi_analysis(self, event_collection, analyses, timeframe=None, timezone=None, filters=None, group_by=None):
        """ Performs a multi-analysis query

        Returns a dictionary of analysis results.

        :param event_collection: string, the name of the collection to query
        :param analyses: dict, the types of analyses you'd like to run.  example:
        {"total money made":{"analysis_type":"sum","target_property":"purchase.price",
        "average price":{"analysis_type":"average","target_property":"purchase.price"}
        :param timeframe: string or dict, the timeframe in which the events
        happened example: "previous_7_days"
        :param timezone: int, the timezone you'd like to use for the timeframe
        and interval in seconds
        :param filters: array of dict, contains the filters you'd like to apply to the data
        example: {["property_name":"device", "operator":"eq", "property_value":"iPhone"}]
        :param group_by: string or array of strings, the name(s) of the properties you would
        like to group you results by.  example: "customer.id" or ["browser","operating_system"]

        """
        params = self.get_params(event_collection=event_collection, timeframe=timeframe, timezone=timezone,
                                 filters=filters, group_by=group_by, analyses=analyses)
        return self.api.query("multi_analysis", params)

    def get_params(self, event_collection=None, timeframe=None, timezone=None, interval=None, filters=None,
                   group_by=None, target_property=None, latest=None, email=None, analyses=None, steps=None):
        params = {}
        if event_collection:
            params["event_collection"] = event_collection
        if timeframe:
            if type(timeframe) is dict:
                params["timeframe"] = json.dumps(timeframe)
            else:
                params["timeframe"] = timeframe
        if timezone:
            params["timezone"] = timezone
        if interval:
            params["interval"] = interval
        if filters:
            params["filters"] = json.dumps(filters)
        if group_by:
            if type(group_by) is dict:
                params["group_by"] = json.dumps(group_by)
            else:
                params["group_by"] = group_by
        if target_property:
            params["target_property"] = target_property
        if latest:
            params["latest"] = latest
        if email:
            params["email"] = email
        if analyses:
            params["analyses"] = json.dumps(analyses)
        if steps:
            params["steps"] = json.dumps(steps)

        return params

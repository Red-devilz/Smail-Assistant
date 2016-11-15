from apiclient.discovery import build


def make_gmail_service(http_auth):
    """ Make gmail_service object for all gmail calls. """
    return build('gmail', 'v1', http=http_auth)


def make_user_service(http_auth):
    """ Make user_service object for user_info calls. """
    return build('oauth2', 'v1', http=http_auth)


def make_calender_service(http_auth):
    return build('calendar', 'v3', http=http_auth)


def list_calendar_events(service):
    """ Returns events from primary calender. """
    return service.events().list(calendarId="primary").execute()


def create_calendar_event(service, data):
    """
    Creates a event in primary calendar.
    Data must be a dict with start, end, name.
    Date format: 2016-11-13T10:30:00+05:30
    """
    body = {
        "creator": {
            "self": False,
            "displayName": "Smail Classifer"
        },
        "summary": data["name"],
        "start": {
            "dateTime": data["start"]
        },
        "end": {
            "dateTime": data["end"]
        }
    }
    return service.events().insert(calendarId="primary", body=body, sendNotifications=True).execute()


def get_user_info(service=None, http_auth=None):
    """
        Returns user info object with name,id,email,picture etc.
    """
    if service is None:
        service = make_user_service(http_auth)
    return service.userinfo().get().execute()


def list_gmail_messages(service, user_info=None, pageToken=None, maxResults=None, q=None):
    """
        Returns messages object with
            messages: list of messages
            nextPageToken: pageToken for rest
            resultSizeEstimate
    """
    args = {'userId': "me"}
    if user_info is not None:
        args['userId'] = user_info['id']
    if pageToken is not None:
        args['pageToken'] = pageToken
    return service.users().messages().list(maxResults=maxResults, q=q, **args).execute()


def get_gmail_message(service, msgId, user_info=None):
    """
        Returns message object with
    """
    args = {'userId': 'me', 'id': msgId}
    if user_info is not None:
        args['userId'] = user_info['id']
    return service.users().messages().get(**args).execute()

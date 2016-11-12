from apiclient.discovery import build


def make_gmail_service(http_auth):
    """ Make gmail_service object for all gmail calls. """
    return build('gmail', 'v1', http=http_auth)


def make_user_service(http_auth):
    """ Make user_service object for user_info calls. """
    return build('oauth2', 'v1', http=http_auth)


def get_user_info(service=None, http_auth=None):
    """
        Returns user info object with name,id,email,picture etc.
    """
    if service is None:
        service = make_user_service(http_auth)
    return service.userinfo().get().execute()


def list_gmail_messages(service, user_info=None, pageToken=None, maxResults=None):
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
    return service.users().messages().list(maxResults=maxResults, **args).execute()


def get_gmail_message(service, msgId, user_info=None):
    """
        Returns message object with
    """
    args = {'userId': 'me', 'id': msgId}
    if user_info is not None:
        args['userId'] = user_info['id']
    return service.users().messages().get(**args).execute()

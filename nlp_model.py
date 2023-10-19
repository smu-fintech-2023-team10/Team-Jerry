def generate_reply(message):
    '''Returns the endpoint based on user's message'''
    #dictionary for routes (key: message, value: endpoint)
    routes = {
        "Check my balance": "/checkBalance",
    }
    
    return routes.get(message, "/unableToFindReply")

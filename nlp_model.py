def generate_reply(message):
    route = "/unableToFindReply"
    if message == "Check my balance":
        route = "/checkBalance"
    return route
import network


def get_status_description(status):
    if status == network.STAT_IDLE:
        return "No connection and no activity"
    elif status == network.STAT_CONNECTING:
        return "Connecting in progress"
    elif status == network.STAT_WRONG_PASSWORD:
        return "Failed due to incorrect password"
    elif status == network.STAT_NO_AP_FOUND:
        return "Failed because no access point replied"
    elif status == network.STAT_CONNECT_FAIL:
        return "Failed due to other problems"
    elif status == network.STAT_GOT_IP:
        return "Connection successful"
    return "Unknown"
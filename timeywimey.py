from parsedatetime import Calendar
import datetime


def epoch2iso(p: int) -> str:
    p = int(p)
    return datetime.datetime.fromtimestamp(p).replace(microsecond=0).strftime("%d. %B %Y %H:%M")


def right_now() -> int:
    return int(datetime.datetime.now().timestamp())  # I have no idea why I am using this, probably has some reason


def parse_time(when: str = "") -> (int, int, int):
    """Return the parsed time in epoch time."""
    cal = Calendar()
    time_struct, parse_status = cal.parse(when)
    if parse_status == 0:
        return 0, 0, 0
    t = datetime.datetime(*time_struct[:6])
    now = right_now()
    try:
        then = int(t.timestamp())  # queryThen
    except OSError:
        then = now
        parse_status = 0
    if then < now + 10:
        parse_status = 0
    return now, then, parse_status


import datetime

def dateparser(datastr):
    if datastr == "":
        return ""
    else:
        if len(datastr) == 10:
            if datastr.find('/') != -1 or datastr.find('-') != -1:
                if datastr.find('/') != 0:
                    day, month, year = datastr.split("/")
                else:
                    day, month, year = datastr.split("-")

                # print("day = %s, month = %s, year = %s" % (day, month, year))
                if int(day) < 31 and int(month) < 12 and int(year) < 3000:
                    date = datetime.date(int(year), int(month), int(day))
                    return date
                else:
                    return -1
            else:
                return -1

        else:
            return -1

def timeparser(timestr):
    if timestr == "":
        return ""
    else:
        if len(timestr) == 5:
            if timestr.find(':') != -1:
                if timestr.find(':') != 0:
                    hour,min = timestr.split(":")
                if int(hour) < 24 and int(min) < 60:
                    time = datetime.time(int(hour), int(min))
                    return time
                else:
                    return -1
            else:
                return -1

        else:
            return -1


def timeDifferenceInSec(date1, date2):
    """Calcolate the difference between 2 dates in second for the alarm."""
    return (date1 - date2).total_seconds()


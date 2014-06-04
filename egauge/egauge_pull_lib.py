#
# 2012 plotwatt.com
#
import logging
import httplib
from datetime import datetime
import calendar

import httplib2


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("eg_pull")

def parse_datetime(str) :
  if str == None :
    return None
  try :
    return datetime.strptime(str, "%Y-%m-%d %H:%M:%S")
  except ValueError :
    try :
      return datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
    except ValueError :
      return datetime.strptime(str, "%Y-%m-%d")
def get_ts(dt):
    return calendar.timegm(dt.utctimetuple())

#
# basic fetch implementation of http://egauge.net/docs/egauge-xml-api.pdf
# 
def egauge_fetch_data(egauge_url, from_time, to_time, username=None, password=None, seconds=False):
  """
  curl -v --digest  -uuser
  'http://egauge2592.egaug.es/cgi-bin/egauge-show?f=1337716679&m&C'

  params
  f: from unix timestamp
  t: to unix tsimestmp
  seconds: fetch 1second granularity data, default is 1 minute
  egauge needs digest authentication
  """
  # f - The timestamp of the first row to be returned
  # t - The timestamp of the last row to be returned
  # The data is in decending order

  gw_url = "http://"+egauge_url+"/cgi-bin/egauge-show"

  if from_time and to_time:
    params = "?f=" + str(to_time) + "&t=" + str(from_time) + "&C"
    if seconds:
      params += "&S"
    else:
      params += "&m"
  else:
    logger.info("-f and -t both are mandatory.")
    return None, None

  logger.info( "Fetching :%s%s "% (gw_url, params))

  # If the DB has value 'NULL' then that maps to 'None' in python object.
  # It gives exception for httplib API's, so set it to "" empty string if they are 'None'
  if username == None:
    username = "owner"
  if password == None:
    password = "default"

  try:
    req = httplib2.Http(timeout=15)
    req.add_credentials(username, password)   # Digest Authentication
    response, content = req.request (gw_url + params, headers={'Connection': 'Keep-Alive', 'accept-encoding': 'gzip'})
    if response['status'] == '401':
      logger.info("Unauthorized request!")
    elif response['status'] == '400':
      logger.info( "Bad Request!")
    elif response['status'] == '500':
      logger.info("Internal Error!")
    elif response['status'] == '408':
      logger.info("Request timeout!")
    elif response['status'] == '404':
      logger.info("device not found. Probably it is not up")

    if response['status'] != '200':
      return None, None
  except httplib.IncompleteRead as e:
    raise(e)
  except Exception as e:
    print e
    return None, None
  return response, content

#
# sample run
#
# python ./egauge_pull_lib.py egauge4077.egaug.es 2012-12-25 2012-12-26
#
if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog device_url from_date to_date [options]")
    parser.add_option("--seconds", default=False, action="store_true",
                    help="will try to fetch seconds data if specified")
    parser.add_option( "--username")
    parser.add_option( "--password")
    (options, args) = parser.parse_args()

    if len(args)<3:
        parser.print_help()
        exit(2)

    device_url = args[0]
    from_str = args[1]
    to_str = args[2]

    from_ts = get_ts(parse_datetime(from_str))
    to_ts = get_ts(parse_datetime(to_str))

    #status, data = egauge_fetch_data('egauge4077.egaug.es',
    #            1356512726,1356612726)

    status, data = egauge_fetch_data(device_url, from_ts, to_ts,
            username=options.username, password=options.password,
            seconds=options.seconds)

    print data


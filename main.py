import psycopg2
from config import config
import pygsheets
import numpy as np
import requests
from datetime import datetime
from cbr_api import api

# запрос курса доллара
# https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=23/06/2022&date_req2=23/06/2022&VAL_NM_RQ=R01235

def get_usd_rate(date_req):
    usd = api.Currency("USD")
    return usd.rate_at_date(date_req)


def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


# service account email
# acc-456@ferrous-quest-354206.iam.gserviceaccount.com
def read_data():
    gc = pygsheets.authorize(service_file="keys/ferrous-quest-354206-5dc0b13a7d61.json")
    sht1 = gc.open_by_key('13J90Tfny9qhpnCkVabyDXIIQ1Ay8GHWOGtpUsk7L4IY')
    wks = sht1.sheet1
    read_df = wks.get_as_df()
    read_df = read_df.reset_index()  # make sure indexes pair with number of rows
    for index, row in read_df.iterrows():
        print(row['№'], row['заказ №'], row['стоимость,$'], row['срок поставки'])


if __name__ == '__main__':
    # connect()
    # read_data()
    print(get_usd_rate(datetime.now().strftime("%d/%m/%Y")))


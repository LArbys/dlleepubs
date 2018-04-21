import os,sys
import psycopg2

PUB_PSQL_ADMIN_HOST="nudot.lns.mit.edu"
PUB_PSQL_ADMIN_USER="tufts-pubs"
PUB_PSQL_ADMIN_ROLE=""
PUB_PSQL_ADMIN_DB="procdb"
PUB_PSQL_ADMIN_PASS=""
PUB_PSQL_ADMIN_CONN_NTRY="10"
PUB_PSQL_ADMIN_CONN_SLEEP="10"

PARAMS = {
  'dbname': PUB_PSQL_ADMIN_DB,
  'user': PUB_PSQL_ADMIN_USER,
  'password': PUB_PSQL_ADMIN_PASS,
  'host': PUB_PSQL_ADMIN_HOST
  }

print PARAMS
CONN = psycopg2.connect(**PARAMS)
CUR = CONN.cursor()                             


def main(argv):

    PROJECT = str(argv[1])

    SS = '''UPDATE %s SET data='';'''
    SS = SS % PROJECT
    print SS
    CUR.execute(SS)
    
    SS = '''UPDATE %s SET status=1;'''
    SS = SS % PROJECT
    print SS
    CUR.execute(SS)
    
    CONN.commit()
    CUR.close()

    return

if __name__ == '__main__':
    main(sys.argv)
    sys.exit(0)
    

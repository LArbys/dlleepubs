import os,sys,commands,datetime
import psycopg2

conn = psycopg2.connect("dbname=procdb user=taritree")
cursor = conn.cursor()

# we get a list of run tables
cursor.execute("select table_name from information_schema.tables")

tablelist = []
others = []
out = cursor.fetchall()
for name in out:
    if "_paths" in name[0]:
        tablelist.append( name[0].strip()[:-6] )
    else:
        others.append(name[0])
tablelist.sort()

projectlist = ["xferinput","tagger","ssnet","freetaggercv","vertex"]
#projectlist = ["xferinput","tagger","ssnet"]
projectstatuscodes = { "xferinput":[1,2,3,None],
                       "tagger":[1,2,4,10],
                       "ssnet":[1,2,4,10],
                       "freetaggercv":[1,2,4,10],
                       "vertex":[1,2,4,10]}

pageheader = """
<!DOCTYPE html>
<html>
<body>
"""

now = datetime.datetime.now()
pagebody = ""
pagebody += "generated at "+now.strftime("%Y-%m-%d %H:%M")+'\n'
pagebody += "<hr>\n"

for table in tablelist:
    
    pagebody += "<h2>"+table+"</h2>\n"

    # get total count
    cursor.execute("select count(*) from %s"%(table))
    count = cursor.fetchone()
    pagebody += "Entries: %d\n"%(int(count[0]))
    # get project info
    pagebody += "<ul>\n"
    for p in projectlist:

        if "%s_%s"%(p,table) not in others:
            #print "not found: ","%s_%s"%(p,table)
            continue
        
        try:
            cursor.execute("select count(*) from %s_%s where status=%d"%(p,table,projectstatuscodes[p][0]))
            tot = int( cursor.fetchone()[0] )
            
            cursor.execute("select count(*) from %s_%s where status=%d"%(p,table,projectstatuscodes[p][1]))
            running = int( cursor.fetchone()[0] )
            
            cursor.execute("select count(*) from %s_%s where status=%d"%(p,table,projectstatuscodes[p][2]))
            completed = int( cursor.fetchone()[0] )
            if projectstatuscodes[p][-1] is not None:
                cursor.execute("select count(*) from %s_%s where status=%d"%(p,table,projectstatuscodes[p][3]))
                error = int( cursor.fetchone()[0] )
            else:
                error = 0
            pagebody += " <li> project %s: Unprocessed %d, Running %d, Completed %d, Error %d</li>\n"%(p,tot, running,completed, error)
        except:
            continue
    pagebody += "</ul>\n"
    
    pagebody += "<hr>\n"


pagefooter = """
</body>
</html>
"""


page = open("dlleepubsummary.html",'w')
print>>page,pageheader
print>>page,pagebody
print>>page,pagefooter
page.close()


os.system("cp dlleepubsummary.html /var/www/html/taritree/")

import re
import mysql.connector
import nltk
import json
from tika import parser
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
#nltk.download('stopwords')
sw=stopwords.words("english")
#database configuration
fd=open('./dbconfig.json')
conf=json.load(fd)
config=conf["dbcon"]
host=conf["host"]
fd.close()

def extractdata(path):
    data=parser.from_file(path)
    data=data['content']
    data=" ".join(data.split())
    return data

def generatengrams(data,n):
    data=re.sub(r'[^a-zA-Z0-9\s]',' ',data)
    tokens=[token for token in data.split(" ") if token!=""]
    ngrams=zip(*[tokens[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]

def cleaning(data):
    data=data.lower()
    words=word_tokenize(data)
    words_wo_stopwords=[word for word in words if not word in sw]
    d=" ".join(words_wo_stopwords)
    return d

def generaterandomjobs():
    # jobid=['JD101','JD102','JD103','JD104','JD105','JD106','JD107','JD108','JD109','JD110']
    # location=['Pune','Hyderabad','Pune','Bangalore','Hyderabad','Bangalore','Pune','Hyderabad','Pune','Bangalore']
    # titles=['Solution Architect','Fullstack Developer','Java Developer','AI Developer','Python Developer','Frontend Developer','Devops Engineer','Cloud Architect','Data Analyst','Programmer Analyst']
    jdquery="SELECT * FROM job_description"
    listofjobs=[]
    conn=mysql.connector.connect(**config)
    sqlquery="SELECT * FROM uploaded_resumes where job_id=%s"
    mycur2=conn.cursor()
    mycur2.execute(jdquery)
    res=mycur2.fetchall()
    listofjobs=[]
    conn=mysql.connector.connect(**config)
    sqlquery="SELECT * FROM uploaded_resumes where job_id=%s"
    if conn.is_connected():
        mycur=conn.cursor()
        for i in res:
            d={}
            d["jobCode"]=i[0]
            d["designationTitle"]=i[1]
            d["location"]=i[5]
            val=(i[0],)
            mycur.execute(sqlquery,val)
            res=mycur.fetchall()
            d["totalUploadedResumes"]=len(res)
            listofjobs.append(d)
    print(listofjobs)
    return listofjobs

def getkeywords(id):
    conn=mysql.connector.connect(**config)
    sqlquery="SELECT job_keywords FROM job_description WHERE id=%s"
    val=(id,)
    try:
        if conn.is_connected():
            cur=conn.cursor()
            cur.execute(sqlquery,val)
            res=cur.fetchone()
        return res[0]
    except mysql.connector.Error as err:
        return ('Database Error: {0}'.format(err))

# def extract_entities(data):
#     nlp = spacy.load('en_core_web_sm')
#     d=nlp(data)
#     entity=[]
#     for ent in d.ents:
#         entity.append(ent.text)
#     entity=" ".join(entity)
#     return entity

def measure_similarity(x,y):
    # vectorizer=TfidfVectorizer()
    # t1=vectorizer.fit_transform(x)
    # t2=vectorizer.fit_transform(y)
    # sim=cosine_similarity(t1,t2)
    common=set.intersection(set(x),set(y))
    union=set.union(set(x),set(y))
    print(list(common))
    sim=len(common)/len(y)
    return sim

def update_humanreview(id,value):
    updatequery="UPDATE uploaded_resumes SET human_review=%s WHERE id=%s"
    val=(value,id)
    conn=conn=mysql.connector.connect(**config)
    try:  
        if conn.is_connected():
            cur=conn.cursor()
            cur.execute(updatequery,val)
            conn.commit()
        return
    except mysql.connector.Error as err:
        print('Database Error: {0}'.format(err))

def getjodId(id):
    conn=conn=mysql.connector.connect(**config)
    try:
        if conn.is_connected():
            cur=conn.cursor()
            selectquery="SELECT job_id FROM uploaded_resumes WHERE id=%s"
            val=(id,)
            cur.execute(selectquery,val)
            res=cur.fetchone()
            conn.close()
        return res[0]
    except mysql.connector.Error as err:
        print('Database Error:{0}'.format(err))


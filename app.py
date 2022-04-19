from flask import Flask,render_template,request,jsonify
from flask_cors import CORS
import os
#os.environ['TIKA_SERVER_JAR'] = 'E:\PYTHON\tika\tika-server-1.27.jar'
import json
import zipfile
from mysql.connector import connection
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import DatabaseError, custom_error_exception
from tika import parser
from datetime import datetime
from models import generatengrams,generaterandomjobs,extractdata,cleaning,getkeywords, measure_similarity,update_humanreview,getjodId
from werkzeug.utils import redirect, secure_filename
import mysql.connector
UPLOAD_FOLDER = './static'
n_grams=[1,2,3]
tper=50
app=Flask(__name__)
app.config['DEBUG']=True
#database configuration
fd=open('./dbconfig.json')
conf=json.load(fd)
config=conf["dbcon"]
host=conf["host"]
fd.close()
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
CORS(app)
#<--------------------Home------------------------>
@app.route('/')
def home():
    return render_template('upload.html')

#<--------------Get list of job openings-------------->
@app.route('/getlistofjobs',methods=['GET'])
def getlistofjobs():
    try:
        data=generaterandomjobs()
        return jsonify(data)
    except DatabaseError as err:
        return jsonify('{0} Encountered!!'.format(err))

#<--------------Getting Job Details....--------------->

@app.route('/getjobdetails/<id>',methods=['GET'])
def getjobdetails(id):    
    try:
        conn=mysql.connector.connect(**config)
        if conn.is_connected():
            mycur=conn.cursor()
            sql="SELECT * FROM job_description where id=%s"
            val=(id,)
            mycur.execute(sql,val)
            data=dict(zip(mycur.column_names,mycur.fetchone()))
            resp=data["responsibilities"]
            resp=resp.split('\r\n')
            resquery="SELECT resume_name from uploaded_resumes where job_id=%s"
            mycur.execute(resquery,val)
            resumes=mycur.fetchall()
            #resumes=resumes.split('\r\n')
            rlist=[]
            for i in resumes:
                rlist.append(i[0])
            #rlist=json.dumps(rlist)
            rdic=[]
            #print(rlist)
            for i in rlist:
                d={}
                d[i]="NULL"
                #json.dumps(d)
                rdic.append(d)
            rdic=json.dumps(rdic)
            print(rdic)
            data["responsibilities"]=resp
            conn.close()
        return data
    except mysql.connector.Error as err:
        return jsonify('Something Went Wrong!!!{0}'.format(err))
#<------------------uploading Resumes---------------------->
@app.route('/uploadresumes/<id>',methods=['POST'])
def resumesupload(id):
    try:
        path=os.path.join(UPLOAD_FOLDER,'uploadedresumes')
        ct=datetime.now().date()
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)
        conn=mysql.connector.connect(**config)
        if conn.is_connected():
            if request.method=='POST':
                mycur=conn.cursor()
                sqlquery="INSERT INTO uploaded_resumes (resume_name,job_id,created_on,created_by) VALUES (%s,%s,%s,%s)"
                if request.files.getlist("folder"):
                    totval=[]
                    files=request.files.getlist('folder')
                    for file in files:    
                        fname=os.path.basename(file.filename)
                        fs=os.path.join(path,secure_filename(fname))
                        if os.path.exists(fs):
                            val=(os.path.basename(fs),id,ct,'vishnu')
                            totval.append(val)
                        else:
                            val=(os.path.basename(fs),id,ct,'vishnu')
                            totval.append(val)
                            file.save(fs)
                    mycur.executemany(sqlquery,totval)
                    conn.commit()
                    conn.close()
                else:
                    files=request.files.getlist("file")
                    totval=[]
                    for file in files:
                        if file.filename.endswith('.zip'):
                            temppath=os.path.join(path,secure_filename(file.filename))
                            file.save(temppath)
                            zip=zipfile.ZipFile(temppath)
                            zipfiles=zip.namelist()
                            with zipfile.ZipFile(temppath,'r') as z:
                                z.extractall(path)
                            for f in zipfiles:
                                val=(f,id,ct,'riya')
                                totval.append(val)
                                mycur.execute(sqlquery,val)
                                conn.commit()
                        else:
                            fname=secure_filename(file.filename)
                            fs=os.path.join(path,secure_filename(file.filename))
                            if os.path.exists(fs):
                                val=(fname,id,ct,'abhiroop')
                            else:
                                val=(fname,id,ct,'abhiroop')
                                file.save(fs)
                            mycur.execute(sqlquery,val)
                            conn.commit()
                    conn.close()
        return jsonify('Inserted!!!')
    except mysql.connector.Error as err:
        return jsonify('Something Went Wrong {0}'.format(err))
        
#<-----------------Screening Resumes-------------------->

@app.route('/screenresumes/<id>',methods=['GET'])
def resumescreening(id):
    try:
        if os.path.exists(copy_path):
            conn=mysql.connector.connect(**config)
            sqlquery="SELECT * FROM uploaded_resumes WHERE job_id=%s"
            val=(id,)
            if conn.is_connected():
                cur=conn.cursor()
                cur.execute(sqlquery,val)
                res=cur.fetchall()
            rname=str(res[0][1])
            folder=rname.split('/')
            if len(folder)>1:
                foldername=folder[0]
            else:
                foldername=""
            screen_data={}
            screen_data["totalUploadedResumes"]=len(res)
            keywords=getkeywords(id)
            screen_data["JD Keywords"]=keywords
            shortlisted=[]
            rejected=[]
            keywords=keywords.split(',')
            print(keywords)
            keywords=" ".join(keywords)
            #keywords=cleaning(keywords)
            print(foldername)
            path=os.path.join(copy_path,foldername)
            if len(foldername)>0:
                for file in os.scandir(path):
                    for i in res:
                        rname=str(i[1]).split('/')[1]
                        if file.name==rname:
                            d={}
                            # cnames=file.name.split('_')
                            # print(cnames)
                            # if len(cnames)>0:
                            #     cname=cnames[1]
                            # else:
                            #     cname=file.name.split('.')[0]
                            if len(res)>0:
                                cname=file.name.split('.')[0]
                            else:
                                cname=""
                            d["resumeName"]=cname
                            d["uploadedOn"]=i[3]
                            data=extractdata(file.path)
                            cleaned_data=data
                            #cleaned_data=cleaning(data)
                            #entities=extract_entities(cleaned_data)
                            #print(entities)
                            sl=[]
                            for j in n_grams:
                                resume_ngrams=generatengrams(cleaned_data,j)
                                keywords_ngrams=generatengrams(keywords,j)
                                sim=measure_similarity(resume_ngrams,keywords_ngrams)
                                sl.append(sim*j)
                            similarity=max(sl)
                            similarity=similarity*100
                            print(similarity)
                            #s=s+similarity
                            d["resumedId"]=i[0]
                            d["keywordsMatch"]=similarity
                            d["isHumanReviewed"]=i[5]
                            d["resumePath"]='static'+'/'+'uploadedresumes'+'/'+foldername+'/'+file.name
                            if i[5]=='Y':
                                #update_humanreview(i[0],'N')
                                shortlisted.append(d)
                            elif similarity>tper and i[5]=='N':
                                rejected.append(d)
                                #update_humanreview(i[0],'N')
                            elif similarity>tper:
                                shortlisted.append(d)
                            else:
                                rejected.append(d)
            else:
                for file in os.scandir(os.path.join(copy_path,foldername)):
                    for i in res:
                        if file.name==i[1]:
                            d={}
                            # cnames=file.name.split('_')
                            # if len(cnames)>1:
                            #     cname=cnames[1]
                            # else:
                            #     cname=file.name.split('.')[0]
                            if len(res)>0:
                                cname=file.name.split('.')[0]
                            else:
                                cname=""
                            d["resumeName"]=cname
                            d["uploadedOn"]=i[3]
                            data=extractdata(file.path)
                            #cleaned_data=cleaning(data)
                            cleaned_data=data
                            sl=[]
                            for j in n_grams:
                                resume_ngrams=generatengrams(cleaned_data,j)
                                keywords_ngrams=generatengrams(keywords,j)
                                sim=measure_similarity(resume_ngrams,keywords_ngrams)
                                sl.append(sim*j)
                            similarity=max(sl)
                            similarity=similarity*100
                            print(similarity)
                            d["resumeId"]=i[0]
                            #s=s+similarity
                            d["keywordsMatch"]=similarity
                            d["isHumanReviewed"]=i[5]
                            d["resumePath"]='static'+'/'+'uploadedresumes'+foldername+'/'+file.name
                            if i[5]=='Y':
                                #update_humanreview(i[0],'N')
                                shortlisted.append(d)
                            elif similarity>tper and i[5]=='N':
                                rejected.append(d)
                                #update_humanreview(i[0],'N')
                            elif similarity>tper:
                                shortlisted.append(d)
                            else:
                                rejected.append(d)
            screen_data["shortlisted"]=shortlisted
            screen_data["rejected"]=rejected
            conn.close()
        return screen_data
    except OSError as err:
        return jsonify('Os Error: {0}'.format(err))
    except mysql.connector.Error as err:
        return jsonify('Database Error: {0}'.format(err))
    except:
        return jsonify('Undefined variable')
    

#<-----------------Human Review------------------->
# Please Enter URL like this http://localhost:5000/humanreview?resumeId=1193&humanreview=false   

@app.route('/humanreview',methods=['GET','POST'])
def human_review():
    try:
        arguments=request.args.to_dict()
        id=arguments["resumeId"]
        ishumanreviewed=arguments["humanreview"]
        conn=mysql.connector.connect(**config)
        if conn.is_connected():
            if ishumanreviewed=='false':
                update_humanreview(id,'N') 
            if ishumanreviewed=='true':
                update_humanreview(id,'Y')
        return jsonify('Completed!!!!')
    except mysql.connector.Error as err:
        return jsonify('Database Error: {0}'.format(err))
    except:
        return jsonify('Mismatched Arguments!!!')


if __name__ == '__main__':
    #creating example folder to store the data
    copy_path=os.path.join(UPLOAD_FOLDER,'uploadedresumes')
    jsonpath=os.path.join(UPLOAD_FOLDER,'json')
    app.run(host='0.0.0.0',port=5001)
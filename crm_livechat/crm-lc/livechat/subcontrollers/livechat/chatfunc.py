from turbogears import controllers, expose, flash, redirect,config
import cherrypy
from cherrypy import request, response
import sha, time
import sys,os,xmpp
import signal
import thread
import xmlrpclib
from livechat import rpc, common
from livechat.rpc import *


cnhost = config.get('cnhost', path="crm")
cnport = config.get('cnport', path="crm")
cntype = config.get('cntype', path="crm")

rpc.session = rpc.RPCSession( cnhost, cnport, cntype , storage=cherrypy.session)

class ChatFunc(controllers.RootController):

    dbname = config.get('dbname', path="crm")
    dbuser = config.get('dbuser', path="crm")
    dbpwd = config.get('dbpwd', path="crm")


    @expose(template="livechat.templates.welcome")
    def index(self):
        print "\n","*"*50,"\nPlease CHECK the Settings in 'dev.cfg'...\n","*"*50,"\n"
        res = rpc.session.login(self.dbname, self.dbuser, self.dbpwd)
        raise redirect('/select_topic')

    @expose(template="livechat.templates.chat_box")
    def chatbox(self):
        pass
        return dict(msglist = self.msglist)

    @expose(format='json')
    def chatbox2(self):
        pass
        print "chatbox2 called"
        return dict(msglist = self.msglist)

    @expose(template="livechat.templates.main_page")
    def select_topic(self,**kw):
            proxy = rpc.RPCProxy("crm_livechat.livechat")
            ids = proxy.search([('name','not like','Dummy'+"%"),('state','=','active')])
            print "IDS",ids
            res = proxy.read(ids, ['id','name','state','max_per_user'])
            print "This is ",res
            return dict(topiclist = res)


    @expose()
    def start_chat(self,**kw):
        cl=''
        topicid = kw.get('topicid')
        print "toppicid:::",topicid
        message = self.mainhandler(cl,topicid)
        print "======message========",message
        return dict(message=message)

    @expose(template="livechat.templates.chat_window")
    def chat_window(self):
        return dict()

    def mainhandler(self,cl,topicid):
        print "Getting in MainHandler..."
#        partners = rpc.RPCProxy("crm_livechat.livechat.partner").search([('name','like','Bond'])

        if not (self.client):
            print "Connection Not Found...  Making Connection again...\n"
            cl = self.myConnection(topicid)
            if cl=='NoActive':
                print "No user left"
                return "Maximum Number of Connection exhausted."
            elif cl == 'ConError':
                print "Failed to Connect..."
                return "Failed to Connect."
            else:
                print "\nStarting Thread to Recieve...."
                self.cont = True
                thread.start_new_thread(self.recieving,("Recieving",5,cl))
        else:
            print "MainHandler Called"
        return "Active"




    def recieving(self,string,sleeptime,cl,*args):
        while self.cont:
            self.recthread = os.getpid()
            try:
                v = cl.Process(1)
            except KeyboardInterrupt:
                return 0
                time.sleep(sleeptime)
        print "Ending Receiving Thread"
        self.cont = True
        return 0

    @expose()
    def close_chat(self, **kw):
       if (kw.get('close')):
           res = rpc.RPCProxy('crm_livechat.livechat').stop_session(int(self.topicid),int(self.sessionid))
           if(self.client):
               self.client.disconnect()
               self.client=None
           self.cont = False
       return {}

    @expose(format='json')
    def justsend(self,**kw):
        print "kw:::::::::::",kw
        sendto = ''
        msg = kw.get('messg')
        if(self.user):
            print "sending",msg," :to:  ",self.user
            sendto = self.user
        print "sendto:::",sendto
        self.recepients = sendto
        self.client.send(xmpp.protocol.Message(sendto,msg))
        msgformat = (str(self.login) + " : "+ str(msg),'sender')
        print msgformat,"::::::"
        self.msglist.append(msgformat)
        print "returning"
        return dict()

    def myConnection(self,topicid):
        cr = ''
        uid = ''
        self.topicid = topicid
        print ">>>>>>>>>>>>>",topicid
        livechatdata = rpc.RPCProxy('crm_livechat.livechat').get_configuration(topicid)
        if livechatdata:
            print "This is first live chat data",livechatdata
            partnerlist = livechatdata['partner']
            pp=map(lambda p:p,partnerlist)
            print "////////////////////////",pp
            jid = livechatdata['partner'][pp[0]]['login']

            print "////////////////////////",jid
            self.login = jid
            pwd = livechatdata['partner'][pp[0]]['password']
            print "making connection with::",jid," and pwd :::",pwd
            jid=xmpp.protocol.JID(jid)
            cl=xmpp.Client(jid.getDomain(),debug=[])


            x = cl.connect()
            if x == "":
                print " Not Connected  \n Connection Error....."
                return "ConError"
            else:
                print "Connected....\nStarting to Authenticate!!!!!!!!!!!!!!...."

                try:
                    auth = cl.auth(jid.getNode(),pwd,"test")
                except AttributeError, err:
                    raise common.error(_("Connection refused !"), _("%s \n Verify USERNAME and PASSWORD in Jabber Config" % err))

                print "cl Authenticated...."
                cl.RegisterHandler('message', self.messageCB)
                cl.sendInitPresence();
                self.client=cl
                print "This is live chat data:",livechatdata,topicid
                user = rpc.RPCProxy('crm_livechat.livechat').get_user([int(topicid)])
                print "\n\n\n\nThe user i get :",user
                user = livechatdata['user'][str(user)]['login']
                self.user= user

                if(self.user):
        #            for x in livechatdata['partner'].keys()
        #                print x
                    print "yyY",pp
                    self.sessionid = rpc.RPCProxy('crm_livechat.livechat').start_session([int(topicid)], False,pp[0])
                    print "\nCreating Session ........";
        else:
            cl="NoActive"
        return cl

    def messageCB(self,conn,msg):
        print "Messge Arriving", msg
        print "\nContent: " + str(msg.getBody())
        print "Sender: " + str(msg.getFrom())
        msgformat = ( str(msg.getFrom()) + " : "+str(msg.getBody()), 'receiver')
        self.msglist.append(msgformat)

    client = None
    recepients=[]
    msglist=[]
    user = ''
    sessionid = ''
    topicid = ''
    mainthread = ''
    recthread = ''
    login = ''
    cont = True


# #!/usr/bin/python2.7

from tkinter import *
from tkinter.ttk import *
import tkinter as tk
import tkinter.ttk

from cryptography.fernet import Fernet
import socket
import _thread

class ChatClient(Frame):

  
  def __init__(self, root):
    Frame.__init__(self, root)
    self.root = root
    self.UI()
    self.serverSoc = None
    self.serverStatus = 0
    self.buffsize = 10000
    self.allClients = {}
    self.counter = 0
  
  def UI(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]

    self.root.title("CryptChat")
    # ScreenSizeX = self.root.winfo_screenwidth()
    # ScreenSizeY = self.root.winfo_screenheight()
    ScreenSizeX = 1920
    ScreenSizeY = 1080
    self.FrameSizeX  = 825
    self.FrameSizeY  = 540
    FramePosX   = int((ScreenSizeX - self.FrameSizeX)/2)
    FramePosY   = int((ScreenSizeY - self.FrameSizeY)/2)
    self.root.geometry("%sx%s+%s+%s" % (self.FrameSizeX, self.FrameSizeY, FramePosX, FramePosY))
    self.root.resizable(width=False, height=False)
    
    padX = 10
    padY = 10
    parentFrame = tk.Frame(self.root)
    parentFrame.grid(padx=padX, pady=padY, stick=E+W+N+S)
    
    ipGroup = Frame(parentFrame)
    serverLabel = Label(ipGroup, text="Set up Server: ")
    head = Label(ipGroup, text="Chat Log: ")
    head1 = Label(ipGroup, text="Connected To: ")
    self.serverIPVar = StringVar()
    self.serverIPVar.set(ip)
    serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
    self.serverPortVar = StringVar()
    self.serverPortVar.set("8091")
    serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
    serverSetButton = Button(ipGroup,text="Set", width=10, command=self.handleSetServer)
    addClientLabel = Label(ipGroup, text="Add friend: ")
    self.clientIPVar = StringVar()
    self.clientIPVar.set("")
    clientIPField = Entry(ipGroup, width=15, textvariable=self.clientIPVar)
    self.clientPortVar = StringVar()
    self.clientPortVar.set("8092")
    clientPortField = Entry(ipGroup, width=5, textvariable=self.clientPortVar)
    clientSetButton = Button(ipGroup, text="Add", width=10, command=self.handleAddClient)
    self.friends = Listbox(ipGroup, bg="gray", width=20, height="1")
    
    serverLabel.grid(row=0, column=0)
    serverIPField.grid(row=0, column=1, sticky=W)
    serverPortField.grid(row=0, column=1, sticky=E)
    serverSetButton.grid(row=0, column=3, padx=5)
    addClientLabel.grid(row=0, column=4)
    clientIPField.grid(row=0, column=5)
    clientPortField.grid(row=0, column=6)
    clientSetButton.grid(row=0, column=7, padx=5)
    head.grid(row=2, column=0)
    head1.grid(row=1, column=0)
    self.friends.grid(row=1, column=1)
    
    readChatGroup = Frame(parentFrame)
    self.receivedChats = Text(readChatGroup, bg="gray", width=100, height=20, state=DISABLED)
    self.receivedChats.grid(row=0, column=0, sticky=W)
    
    writeChatGroup = Frame(parentFrame)
    self.chatVar = StringVar()
    self.chatField = Entry(writeChatGroup, width=75, textvariable=self.chatVar)
    sendChatButton = Button(writeChatGroup, text="Send", width=10, command=self.handleSendChat)
    self.chatField.grid(row=0, column=0, sticky=W)
    sendChatButton.grid(row=0, column=1, padx=5)
    self.root.bind('<Return>', self.handleSendChat)

    self.statusLabel = Label(parentFrame)

    bottomLabel = Label(parentFrame, text="Simple P2P chat application")
    
    ipGroup.grid(row=0, column=0)
    readChatGroup.grid(row=1, column=0)
    writeChatGroup.grid(row=2, column=0, pady=10)
    self.statusLabel.grid(row=3, column=0)
    bottomLabel.grid(row=4, column=0, pady=10)
    
  def handleSetServer(self):
    if self.serverSoc != None:
        self.serverSoc.close()
        self.serverSoc = None
        self.serverStatus = 0
    serveraddr = (self.serverIPVar.get().replace(' ',''), int(self.serverPortVar.get().replace(' ','')))
    try:
        self.serverSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSoc.bind(serveraddr)
        self.serverSoc.listen(1)
        self.setStatus("Server listening on %s:%s" % serveraddr)
        _thread.start_new_thread(self.listenClients,())
        self.serverStatus = 1
    except:
        self.setStatus("Error setting up server")
        
  def listenClients(self):
    while 1:
      clientsoc, clientaddr = self.serverSoc.accept()
      self.setStatus("Client connected from %s:%s" % clientaddr)
      self.addClient(clientsoc, clientaddr)
      _thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr))
    self.serverSoc.close()
  
  def handleAddClient(self):
    if self.serverStatus == 0:
      self.setStatus("Set server address first")
      return
    clientaddr = (self.clientIPVar.get().replace(' ',''), int(self.clientPortVar.get().replace(' ','')))
    try:
        clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsoc.connect(clientaddr)
        self.setStatus("Connected to client on %s:%s" % clientaddr)
        self.addClient(clientsoc, clientaddr)
        _thread.start_new_thread(self.handleClientMessages, (clientsoc, clientaddr))
    except:
        self.setStatus("Error connecting to client")

  def handleClientMessages(self, clientsoc, clientaddr):
    while 1:
      try:
        data = clientsoc.recv(self.buffsize)
        if not data:
          break
        self.addChat("%s:%s" % clientaddr, data)
      except:
          break
    self.removeClient(clientsoc, clientaddr)
    clientsoc.close()
    self.setStatus("Client disconnected from %s:%s" % clientaddr)

  def handleSendChat(self, event=None):  

    if self.serverStatus == 0:
      self.setStatus("Set server address first")
      return
    msg = self.chatVar.get()
    if msg == '':
      return
    if self.counter == 0:
      return
    key = '4Li4zGqWckAsENtH7B0HlKMwXvTLbaJ7Xq-QuKmTbhM='
    cipher_suite = Fernet(key)
    msg = cipher_suite.encrypt(msg)
    self.addChat("Me", msg)
    for client in self.allClients.keys():
      client.send(msg)
      self.chatField.delete(0, 'end')
      

  
  def addChat(self, client, msg):
    self.receivedChats.config(state=NORMAL)
    key = '4Li4zGqWckAsENtH7B0HlKMwXvTLbaJ7Xq-QuKmTbhM='
    cipher_suite = Fernet(key)
    msg = cipher_suite.decrypt(msg)
    self.receivedChats.insert("end",client+"#> "+msg+"\n")
    self.receivedChats.config(state=DISABLED)
    
    
  
  def addClient(self, clientsoc, clientaddr):
    self.allClients[clientsoc]=self.counter
    self.counter += 1
    self.friends.insert(self.counter,"%s:%s" % clientaddr)
  
  def removeClient(self, clientsoc, clientaddr):
      print (self.allClients)
      self.friends.delete(self.allClients[clientsoc])
      del self.allClients[clientsoc]
      print (self.allClients)
  
  def setStatus(self, msg):
    self.statusLabel.config(text=msg)
    print (msg)
      
def main():  
    root = Tk()
    app = ChatClient(root)
    root.mainloop()  

if __name__ == '__main__':
  main()

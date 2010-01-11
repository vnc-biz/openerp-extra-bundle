import sys
import chilkat
import os

def generateEML(mail):
    sub = (mail.Subject).replace(' ','')
    body = mail.Body.encode("utf-8")
    recipients=mail.Recipients
    sender=mail.SenderEmailAddress
    attachments=mail.Attachments

    email = chilkat.CkEmail()
    email.put_Subject(str(sub))
    email.put_Body(str(body))
    email.put_From(str(sender))

    for i in xrange(1, recipients.Count+1):
        name = str(recipients.Item(i).Name)
        address = str(recipients.Item(i).Address)
        email.AddTo(name,address)

    eml_name=sub+'-'+str(mail.EntryID)[-9:]
    ls = ['*', '/', '\\', '<', '>', ':', '?', '"', '|']

    attachments_folder_path = os.path.abspath(os.path.dirname(__file__)+"\\dialogs\\resources\\attachments\\")
    if not os.path.exists(attachments_folder_path):
        os.makedirs(attachments_folder_path)
    for i in xrange(1, attachments.Count+1):
        fn = eml_name + '-' + attachments[i].FileName
        for c in ls:
            fn = fn.replace(c,'')
        att_file = str(os.path.join(attachments_folder_path, fn))
        if os.path.exists(att_file):
            os.remove(att_file)
        attachments[i].SaveAsFile(att_file)
        contentType = email.addFileAttachment(att_file)
        if (contentType == None ):
            print mail.lastErrorText()
            sys.exit()

    mails_folder_path = os.path.abspath(os.path.dirname(__file__)+"\\dialogs\\resources\\mails\\")
    if not os.path.exists(mails_folder_path):
        os.makedirs(mails_folder_path)
    for c in ls:
        eml_name = eml_name.replace(c,'')
    eml_path = str(os.path.join(mails_folder_path,eml_name+".eml"))
    success = email.SaveEml(eml_path)
    if (success == False):
        print email.lastErrorText()
        sys.exit()

    print "Saved EML!"
    return eml_path
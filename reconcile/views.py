from django.shortcuts import render
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.storage import default_storage


import re

from reconcile.forms import RegisterForm
 

def homepage(request):
	return render(request = request,
				template_name = "reconcile/home.html",
				context={})


def register(request):
	if request.method == "POST":
		form = RegisterForm(request.POST)
		if form.is_valid():
			user = form.save()
			username = form.cleaned_data.get("username")
			messages.success(request, f"New account created: {username}")
			login(request, user)
			return redirect("reconcile:account")

		else:
			for msg in form.error_messages:
				messages.error(request, f"{msg}: {form.error_messages[msg]}")

			return render(request = request,
						  template_name = "reconcile/register.html",
						  context={"form":form})


	form = RegisterForm()
	return render(request = request,
				template_name = "reconcile/register.html",
				context={"form":form})


def logout_request(request):
	logout(request)
	messages.info(request, "Logged out successfully!")
	return redirect("reconcile:homepage")


def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request=request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get("username")
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}")
				return redirect('reconcile:account')
			else:
				messages.error(request, "Invalid username or password.")
	else:
		messages.error(request, "Invalid username or password.")		


	form = AuthenticationForm()
	return render(request = request,
			template_name = "reconcile/login.html",
			context={"form":form})


# Custom Functions Start
def newDateForm(date):
    newDate = date[6:] + '/' + date[4:6] + '/' + date[0:4]
    return newDate


def newTimeForm(time):
    newTime = ''
    if int(time[:2]) > 12:
        h = int(time[:2]) - 12
        newTime = str(h) + time[2:] + 'pm'
    elif int(time[:2]) == 12:
        newTime = time + 'pm'
    elif int(time[:2]) == 0:
        h = int(time[:2]) + 12
        newTime = str(h) + time[2:] + 'am'
    else:
        newTime = time + 'am'
    return newTime            


def fileToList(atm_file):
	newString = []
	for line in atm_file:
		newString.append(line.replace('\n', ''))
				
	return newString

def transactionStart(data):
    cardIn = re.compile(r'TK\d\:(\d){6}\.+\d+$')
    mo = list(filter(cardIn.search, data))
    return mo

def transactionEnd(data):
    cardtaken = re.compile(r'\((\d){6}\.+\d+\)')
    mot = list(filter(cardtaken.search, data))
    return mot

        
def getCardTransaction(data, cardin, cardtaken):
    cardTransaction = []
    
    for i in range(len(cardin)):
         cardNumReg = re.compile(r'TK\d\:(\d){6}\.+\d+$')
         mo = cardNumReg.search(cardin[i])
         preCardNum = mo.group()
         cardNum = preCardNum[4:]

         if cardNum in cardin[i] and cardNum in cardtaken[i]:
            
            #save the items in a variable
            a = cardin[i]
            b = cardtaken[i]
            
            #find the index of each item in the main log file
            ai = data.index(a)
            bi = data.index(b)
            
            #adjust the starting and ending index
            nai = ai - 8
            nbi = bi + 8

            cardTransaction.append(data[nai:nbi])
            
    return cardTransaction


def getSuccessfulTransaction(tsgList):
    success = []
    for i in range(len(tsgList)):
        sRegex = re.compile(r'\:Wait\sfor\scash\staken$')
        mo = list(filter(sRegex.search, tsgList[i]))
        strmo = "".join(mo)
        if strmo:
            success.append(tsgList[i])
    return success


def getFailedTransaction(tsgList):
    fail = []
    for i in range(len(tsgList)):
        sRegex = re.compile(r'\:Wait\sfor\scash\staken$')
        mo = list(filter(sRegex.search, tsgList[i]))
        strmo = "".join(mo)
        if not strmo:
            fail.append(tsgList[i])
    return fail


#pass in the list of all card transactions from above
def htmlCardsTsgView(listOfCardTsg):
    holder = []
    for i in range(len(listOfCardTsg)):
        cup = []

        #in each card, check for transaction start and extract the date and time
        dateRegex = re.compile(r'->Transaction start')
        mo = list(filter(dateRegex.search, listOfCardTsg[i]))
        strmo = "".join(mo)
        if strmo:
            pattern = '(\d+:){2}\d+\/\d+$'
            dtmo = re.search(pattern, strmo)
            dt = dtmo.group()
            timeStart = newTimeForm(dt[: dt.index('/')])
            date = newDateForm(dt[dt.index('/') + 1 : ])
            cup.append(date)
            cup.append(timeStart)

        cardNumRegex = re.compile(r'TK\d\:(\d){6}\.+\d+$')
        cardNmo = list(filter(cardNumRegex.search, listOfCardTsg[i]))
        strcardNmo = "".join(cardNmo)
        if strcardNmo:
            patern = '\d+\.+\d+$'
            cardMo = re.search(patern, strcardNmo)
            cardN = cardMo.group()
            cup.append(cardN)
            

        endRegex = re.compile(r'<-Transaction end')
        emo = list(filter(endRegex.search, listOfCardTsg[i]))
        stremo = "".join(emo)
        if stremo:
            patn = '(\d+:){2}\d+\/\d+$'
            dtemo = re.search(patn, stremo)
            dte = dtemo.group()
            timeEnd = newTimeForm(dte[: dte.index('/')])
            cup.append(timeEnd)


        #this checks to see if cash was paid or not
        statusRegex = re.compile(r'R(\d){3}')
        smo = list(filter(statusRegex.search, listOfCardTsg[i]))
        strsmo = "".join(smo)

        #this checks to see if it was a withdrawal or a transfer
        trfReg = re.compile(r'TRANSFER')
        trfMo = list(filter(trfReg.search, listOfCardTsg[i]))
        strtrfMo = "".join(trfMo)

        inqReg = re.compile(r'INQUIRY')
        inqMo = list(filter(inqReg.search, listOfCardTsg[i]))
        strinqMo = "".join(inqMo)
        
        if strsmo:
            pc = strsmo[strsmo.index('R') : ]
            p = '2019\d+\s\d+\s\:'
            pca = re.sub(p, "", pc)
            cup.append(pca)
        elif strtrfMo:
            cup.append("TRANSFER")
        elif strinqMo:
        	cup.append("INQUIRY")
        else:
            cup.append("")
             
        holder.append(cup)

    return holder

def allSuccessfulTsg(sLog):
    holder = []
    for i in range(len(sLog)):
        dataReg = re.compile(r'R000')
        mo = list(filter(dataReg.search, sLog[i]))
        strmo = "".join(mo)

        if strmo:
            pc = strmo[strmo.index('R') : ]
            p = '2019\d+\s\d+\s\:'
            pca = re.sub(p, "", pc)
            
            if pca.count('R000') > 1:
                x = re.compile(r'R0{4}\s+\[\d\]\w+\d+\W\d\W\d+')
                xi = x.findall(pca)
                for i in xi:
                    holder.append(i)
            else:
                holder.append(pca)
    return holder

def totalCashDisp(data):

    counter = 0
    
    for i in range(len(data)):
        r = re.compile(r'\d+$')
        mo = r.search(data[i])
        if not None:
            num = int(mo.group())
            
            counter += num

    return counter			
# Custom Functions End

def account(request):
	if "GET" == request.method:
		return render(request = request,
				template_name = "reconcile/account.html",
				context={})
	
	if request.method == 'POST' and request.FILES["data_file"]:
		myfile = request.FILES["data_file"]
		if not (myfile.name.endswith('.log') or myfile.name.endswith('.txt')):
			messages.error(request, "Filetype is not acceptable")
		else:
			myfile = request.FILES["data_file"]
			filename = default_storage.save(myfile.name, myfile)
			messages.success(request, "File Uploaded Successfully")

			filedata = default_storage.open(filename, 'r')
			fdata = filedata.readlines()
			list_fdata = fileToList(fdata)
			#tsg means transaction
			card_tsg_start = transactionStart(list_fdata)
			card_tsg_end = transactionEnd(list_fdata)
			full_card_tsg = getCardTransaction(list_fdata, card_tsg_start, card_tsg_end)
			cash_taken = getSuccessfulTransaction(full_card_tsg)
			no_cash_taken = getFailedTransaction(full_card_tsg)
			cash_taken_summary = htmlCardsTsgView(cash_taken)
			no_cash_summary =  htmlCardsTsgView(no_cash_taken) 

			disp_data = allSuccessfulTsg(cash_taken)
			dispense_data = totalCashDisp(disp_data)
			
			return render(request = request,
					template_name = "reconcile/account.html",
					context={
					'data': cash_taken_summary,
					'data2' : no_cash_summary,
					'data3' : dispense_data
						}
					)
		

	return render(request = request,
				template_name = "reconcile/account.html",
				context={})


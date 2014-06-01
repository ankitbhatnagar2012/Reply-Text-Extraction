'''
REPLY TEXT EXTRACTION FROM EMAILS
#################################

Techniques Employed :-

(1) SEQUENTIAL TEXT CLIPPING 
		Using custom search structure ( e.g. "....Please reply above this line...." )

(2) NON-SEQUENTIAL LEARNING PRIMITIVES
		Lines starting with pre-defined patterns :- ">", "From", "On <date>" etc
		Deterministic Text Pattern Analysis :- frequent occurences of string in a defined client e.g. "_NextPart_" for MSO
		Maximum Entropy Classifiers :- percentage occurence of a given set of characters

'''
import re
import base64
import quopri
import email.parser
from HTMLParser import HTMLParser

parsedHTMLContent = []

class CustomHTMLParser(HTMLParser):
	def handle_starttag(self, tag, attrs):
		# print "start tag:", tag
    	pass
    def handle_endtag(self, tag):
        # print "end tag :", tag
        pass

    def handle_data(self, data):
        # print data
        parsedHTMLContent.append(data);


def get_reply_string_with_inline_responses(payload, headers, isMultipart):
	con = "NOT_FOUND"
	if isMultipart:
		bodyString = payload.get_payload()
		if 'Content-Transfer-Encoding' in payload.keys():
			con = payload.get('Content-Transfer-Encoding') 
	else:
		'''
		if not multipart, payload itself is the bodyString
		'''
		bodyString = payload

	if con.lower() == "base64":
		bodyString = base64.b64decode(bodyString)
	else:
		bodyString = quopri.decodestring(bodyString)	

	replyString = []
	min_index = max_index = -1

	tempString = bodyString.split('\n')
	
	# first line of reply
	for string in tempString:
		if string.find('>') != -1 and string.index('>') == 0:
			break
		min_index = min_index + 1

	# last line of reply
	temp_index = 0
	for string in tempString:
		if string.find('>') != -1 and string.index('>') == 0:
			max_index = temp_index
		temp_index = temp_index + 1; 

	# building all inline replies
	index = 0
	for string in tempString:
		if index >= min_index and index <= max_index and string.find('>') == -1:
			replyString.append(string)
		index = index+1

	temp = " ".join(string for string in replyString)
	
	return temp.strip()


def get_reply_string_without_custom_message(payload):
	bodyString = payload.get_payload()
	begin_index = bodyString.rfind("On");
	bodyString = bodyString[0:begin_index]
	return bodyString.strip()


def get_reply_string_without_custom_message_v2(payload):
	bodyString = payload.get_payload()

	'''
	stripping all content beyond the end of body content
	'''
	end_index = bodyString.find("--=20") # body delimiter in gmail
	bodyString = bodyString[0:end_index]

	'''
	one alternative idea to strip further could be to find a line | paragraph with majority words from the list below >>> this paragraph needs to be removed.
	'''
	keywords = ['On','Mon','Tues','Wed','Thurs','Fri','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','wrote','AM','PM']

	# setting threshold for the maximum number of characters in the paragraph e.g. n words * m characters each
	threshold = 10*4

	begin_index = len(bodyString)-1
	begin_from = bodyString.find("On");
	max_count = -1
	last_word = ''
		
	while (begin_from+threshold+10) < len(bodyString):
		count = 0
		tempString = bodyString[begin_from:begin_from+threshold+10]
		tempString = tempString.split(' ')
		for word in tempString:
			word = word.split(',')
			word = word[0]
			last_word = word
			if word in keywords:
				count = count + 1

		if(count > max_count):
			max_count = count
			begin_index = begin_from

		'''
		to adjust for the words that might have been left un-considered at the ends >>> wrapping in [ begin_from ... begin_from+100 ]
		'''	
		begin_from = begin_from + threshold - 10

	'''
	that paragraph MOST LIKELY begins from begin_index
	'''
	bodyString = bodyString[0:begin_index]
	
	return bodyString.strip()



def get_reply_string_with_custom_message(payload):
	'''
	this is where reply structure needs to be handled. Different email clients structure reply-emails differently.
	'''
	constMessage = "Please reply above this line" 
	
	bodyString = payload.get_payload()
	
	index = bodyString.lower().rfind(constMessage.lower())
	
	if index == -1:
		replyString = "NOT_FOUND"
	else:
		begin_index = index+len(constMessage)+2
		
		replyString = bodyString[begin_index:]
		
		'''
		trying to find the end of the reply string <<< strictly client dependent

		'''
		# GMAIL REPLY STRUCTURE
		end_index = 0

		'''
		using the learning primitive that the previous messages would begin with a >
		'''
		end_index_1 = replyString.find(">") # quoted previous mail ... assumption that this is a single reply thread
		end_index_2 = replyString.find("--=20") # end of body content .... not generic though
		
		# use whichever delimiter exists earlier
		if end_index_1 < end_index_2:
			end_index = end_index_1
		else:
			end_index = end_index_2

		replyString = replyString[0:end_index]
	
	return replyString.strip()


def isBase64(s):
	return (len(s) % 4 == 0) and re.match('^(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==)$', s)


def get_reply_string_with_custom_message_v2(payload, headers, isMultipart):
    con = "NOT_FOUND"
    if isMultipart:
    	bodyString = payload.get_payload()
    	'''
    	in case of multipart mails, check for the payload's header to identify Content-Type and Content-Transfer-Encoding
    	'''
    	if 'Content-Transfer-Encoding' in payload.keys():
    		con = payload.get('Content-Transfer-Encoding')
    	else:
    		con = "NOT_FOUND"
    
    else:
    	'''
    	if not multipart, payload itself is the bodyString
    	'''
    	bodyString = payload

    # print bodyString
    print "CONTENT-TRANSFER-ENCODING : " + str(con)

    if con.lower() == "base64":
    	bodyString = base64.b64decode(bodyString)
    else:
    	bodyString = quopri.decodestring(bodyString)
    
    
    '''
    checking different custom messages being used. Also account for different translations of the message for i18n
    '''
    index = bodyString.find("Please reply above this line")
    if index == -1:
        index = bodyString.find("Please write your reply above this line")

    if index == -1:
        replyString = "NOT_FOUND"
    else:
        '''
        1. strip by the custom message
        '''
        replyString = bodyString[0:index-1]
        
        '''
        2. strip by the custom message encoding, if at all
        '''
        if con == "quoted-printable":
        	index = replyString.find("=3D=3D=3D=3D=3D")
        	replyString = replyString[0:index-1]
        
        '''
        3. strip by the sent notice
        '''
        index = replyString.rfind("From:")
        replyString = replyString[0:index-1]

        '''
        4. strip by the written notice from the sender
        '''
        index = replyString.rfind("On")
        replyString = replyString[0:index-1]
        
        '''
        5. CLIENT_DEPENDENT_PROCESSING
        '''

        '''

        For MS Outlook

        '''
        if headers['X-Mailer'] is not None and headers['X-Mailer'].lower().find('outlook') != -1:
            
            '''
            check for additional headers in newer versions of outlook > 12.0 :-
            '''
            newer = 0
            index = replyString.lower().find("_NextPart_".lower())
            if index != -1:
            	newer = 1

            if newer:
            	replyString = replyString[index+1+10:]

        	'''
        	further improvement could be searching & stripping all possible values of Content-Type :: standardised constant
        	'''
        	index = replyString.lower().find("Content-Type".lower())
        	replyString = replyString[index+1+15:]

        	'''
        	further improvement could be searching & stripping all possible values of Content-Transfer-Encoding :: standardised constant 
        	'''
        	index = replyString.lower().find("Content-Transfer-Encoding".lower())
        	replyString = replyString[index+1+42:]

        
        '''

        For Lotus Notes
        
        '''
        if headers['X-Mailer'] is not None and headers['X-Mailer'].lower().find('lotus notes') != -1:
            
            '''
            further improvement could be searching & stripping all possible values of Content-Type :: standardised constant
            '''
            index = replyString.lower().find("Content-Type".lower())
            replyString = replyString[index+1+15:]

            '''
            further improvement could be searching & stripping all possible values of Content-Transfer-Encoding :: standardised constant 
            '''
            index = replyString.lower().find("Content-Transfer-Encoding".lower())
            replyString = replyString[index+1+42:]

        

        '''

        For Blackberry
        
        '''
        if headers['X-Mailer'] is not None and headers['X-Mailer'].lower().find('blackberry') != -1:
            
            '''
            since Blackberry encodes messages in the form of HTML, we need to parse HTML in the body string.
            '''
            parser = CustomHTMLParser()
            parser.feed(replyString)
            replyString = ''.join(parsedHTMLContent)
            
            '''
            further improvement could be searching & stripping all possible values of Content-Type :: standardised constant
            '''
            index = replyString.lower().find("Content-Type".lower())
            replyString = replyString[index+1+15:]

            '''
            further improvement could be searching & stripping all possible values of Content-Transfer-Encoding :: standardised constant 
            '''
            index = replyString.lower().find("Content-Transfer-Encoding".lower())
            replyString = replyString[index+1+42:]

            '''
            find and strip remaining Blackberry-specific email headers
            '''
            index = 0
            while index != -1:
            	index = replyString.lower().find("X-".lower())
            	replyString = replyString[index+1+10:]
			
	
	'''
    try and remove all blank lines / spaces at the beginning of lines encoded by the client
    '''
    '''
    temp = []
    tempString = replyString.split("\n")
    for string in tempString :
        if string != "\r" :
            temp.append(string.strip()) 

    replyString = " ".join(temp)
    '''

    return replyString.strip()



def extractUtility(payload, headers, isMultipart):
	
	replyString = get_reply_string_with_custom_message_v2(payload, headers, isMultipart)
	if replyString == "" or replyString == "NOT_FOUND":
		replyString = get_reply_string_with_inline_responses(payload, headers, isMultipart)
		if replyString == "" or replyString == "NOT_FOUND":
			replyString = "Failed"

	'''
	replyString could be in different charsets. The DB-write() needs to incorporate the charset found above.
	'''
	print replyString



def extract(mailString):
	# get email body from the mail string
	parser = email.parser.HeaderParser()
	
	headers = parser.parsestr(mailString)

	if headers['X-Mailer'] is None:
		print "CLIENT USED : NOT_FOUND"
	else:
		print "CLIENT USED : " + str(headers['X-Mailer'])

	message = email.message_from_string(mailString)

	'''
	list all header elements
	'''
	# print message.items();

	replyString = ''

	if message.is_multipart():
		# message under consideration is multipart
		entirePayload = message.get_payload()
		for payload in entirePayload:
			extractUtility(payload, headers, True)
			break
	else:
		# message under consideration in not multipart
		payload = message.get_payload()
		extractUtility(payload, headers, False)


'''
TESTER FUNCTION : get original mail string here and pass to extract()
'''
if __name__ == "__main__":
	x = 1
	while x <= 15:
		filename = str(x) + ".txt"
		f = open(filename,'r')
		mailString = f.read()
		parsedHTMLContent = []
		print "TEST CASE # " + str(x)
		extract(mailString)
		print "######################"
		x = x + 1
		# break
	

'''
parse reply mails with custom message 
'''
# replyString = get_reply_string_with_custom_message(payload)
# replyString = get_reply_string_with_custom_message_v2(payload)

'''
parse reply mails without custom message
'''
# replyString = get_reply_string_without_custom_message(payload)
# replyString = get_reply_string_without_custom_message_v2(payload)

'''
parse reply mails with inline replies
'''
# replyString = get_reply_string_with_inline_responses(payload)




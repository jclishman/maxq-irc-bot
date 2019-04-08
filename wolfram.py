import urllib.request
import urllib.parse
from xml.dom import minidom

wa_key = "INSERT-KEY-HERE"
timeout = str(3)

def get_wa(query):

    query = query.lstrip().rstrip()

    if query == "":
        return "Empty query"

    addr = "http://api.wolframalpha.com/v2/query?appid=" + wa_key + "&input=" +  urllib.parse.quote(query) + "&format=plaintext&podindex=1&podindex=2&scantimeout=" + timeout + "&podtimeout=" + timeout + "&formattimeout=" + timeout + "&parsetimeout=" + timeout + "&units=metric"

    try:
        with urllib.request.urlopen(addr) as url:
            resp = url.read().decode()
            xmlresp = minidom.parseString(resp)
            success = (xmlresp.getElementsByTagName('queryresult')[0].attributes['success'].value == "true")
            error = (xmlresp.getElementsByTagName('queryresult')[0].attributes['error'].value == "true")
            if error:
                print(resp)
                return query + ": Wolfram API returned an error - " + xmlresp.getElementsByTagName('msg')[0].childNodes[0].nodeValue

            if not success:
                return query + ": Seems that Wolfram is unable to understand that."
            
            wolframoutput = ""

            for n in xmlresp.getElementsByTagName('pod'):
                plntxt = ""
                for n2 in n.childNodes:
                    if n2.nodeType == n2.ELEMENT_NODE and n2.tagName == "subpod":
                        for n3 in n2.childNodes:
                            if n3.nodeType == n3.ELEMENT_NODE and  n3.tagName == "plaintext":
                                for n4 in n3.childNodes:
                                    if n4.nodeType == n4.TEXT_NODE:
                                        plntxt += n4.nodeValue
                
                subpod = plntxt.replace("\n", ", ").lstrip().rstrip()

                if n.attributes['title'].value == "Input interpretation":
                    wolframoutput += subpod + ": "
                elif n.attributes['title'].value == "Input":
                    wolframoutput += subpod + " = "
                else:
                    wolframoutput += subpod
            
            return wolframoutput
            
    except urllib.error.HTTPError as e:
        print(str(e))
        return "Wolfram is broken. Ping jclishman."

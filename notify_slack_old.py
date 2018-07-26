import json, sys, os, time, requests
#from slackclient import SlackClient
#set base URL's to access API's
api_base_url = "https://lab-api.nowsecure.com/app"
web_base_url = "https://lab.nowsecure.com/app"

slack_url = os.environ("SLACK_URL")

#define what app to be monitoring
ios_path = '/android/fuzion24.dynamictestapp'
app_url = api_base_url + ios_path
la_token = os.environ("API_KEY")
#Set authorization for Lab Auto API
token = "Bearer " + la_token
headers = {'Authorization': token}

#URL request to get a list of asssesments
assessment_url = app_url + "/assessment/"

#Get a list of assessments from the Lab Auto API and parse the JSON data
r = requests.get(assessment_url, headers=headers)
assessment_list = json.loads(r.text)

#set baseline for current assessments
num_assessments = len(assessment_list)
last_assessment_index = num_assessments - 1

while True:
    #print "Monitoring"
    time.sleep(5)
    r2 = requests.get(assessment_url, headers=headers)
    current_list = json.loads(r2.text)
    #check and see if new assessments have been added
    print "Base assessment: " + str(num_assessments)
    print "Current assessment: " + str(len(current_list))
    if len(current_list) > num_assessments:
        print "New Assessment!"
        #check to make sure the new assessment has finished entirely
        if ((str(current_list[num_assessments]["status"]["static"]["state"]) == "completed") &
        (str(current_list[num_assessments]["status"]["dynamic"]["state"]) == "completed")):
            high = 0
            low = 0
            medium = 0
            info = 0
            print "New completed assesssment, sending report"
            #get the new assessment
            report_url = assessment_url + str(current_list[num_assessments]["task"]) + "/results"
            r3 = requests.get(report_url, headers=headers)
            parsed_report = json.loads(r3.text)

            #loop through the results and increment issue counters
            try:
                for children in parsed_report:
                    try:
                        if children["severity"] == "high":
                            high += 1
                            print children["title"] + " found - high risk"
                        if children["severity"] == "medium":
                            medium += 1
                            print children["title"] + " found - medium risk"
                        if children["severity"] == "low":
                            low += 1
                            print children["title"] + " found - low risk"
                        if children["severity"] == "info":
                            info += 1
                            print children["title"] + " found - info only"
                        title = children["title"]
                    except:
                        pass
            except:
                pass
            print "Parsing complete, creating message"
            #create the slack message
            now = int(time.time())
            color = ""
            if info > 0:
                color = "#808080"
            if low > 0:
                color = "#008080"
            if medium > 0:
                color = "#FFC300"
            if high > 0:
                color = "#FF0000"
            weburl = web_base_url + ios_path + "/assessment/" + str(current_list[num_assessments]["task"])

            slack_data = {
            	"attachments": [
            		{
            			"fallback": "NowSecure Automation",
            			"title": "An application assessment has been run",
            			"color": color,
                        "title_link": weburl,
            			"text": "The following security issues were found:",
            			"fields": [
            				{
            					"value": str(high) + " high risk",
            					"short": "true"
            				},
            				{
            					"value": str(medium) + " medium risk",
            					"short": "true"
            				},
            				{
            					"value": str(low) + " low risk",
            					"short": "true"
            				},
            				{
            					"value":str(info) + " informational",
            					"short": "true"
            				}
            			],
            			"footer": "<!date^" + str(now) + "^{date} at {time}|Error reading date>"
            		}
            	]
            }

            #send the message, move forward one report
            slack_header = 'Content-type: application/json'
            r4 = requests.post(slack_url, json=slack_data,)
            if r4.status_code == 200:
                num_assessments = num_assessments + 1
            else:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s'
                    % (response.status_code, response.text)
)

        else:
            print "Asessment in progress, not completed"
    else:
        print "No new assessments"

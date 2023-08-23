# Team-Jerry
**For Testing**
**Setup**
```
#Install dependencies
pip install -r requirements.txt
pip install firebase-admin --user
#Run
python main.py

```
- Next, you need to install ngrok by just double clicking ngrok.exe

You will see this webhook created for receiving messages from Twilio
```
Session Expires               1 hour, 59 minutes
Version                       2.3.41
Region                        United States (us)
Web Interface                 http://127.0.0.1:4042
Forwarding                    http://f0fb-118-200-109-192.ngrok.io -> http://localhost:5000
Forwarding                    https://f0fb-118-200-109-192.ngrok.io -> http://localhost:5000

```
Copy the webhook with 'https' and change it in the twilio consile + /getReply
e.g. https://f0fb-118-200-109-192.ngrok.io/getReply
![Alt text](images/TwilioConsole-1.png)

**Twilio Account:**
- Username: gerald_4231@hotmail.com
- Password: Gljr4231@Leefamily22

**Join the Twilio sandbox to test on own phone**
Scan the QR code and follow the instructions below
![Alt text](images/TwilioConsole-2.png)

- Change the auth_token to the most recent one as seen in the console.

**Moving Forward**
- Host on AWS or GCP so dont need use webhook as the ngrok webhook always changes everytime the app is re-ran, then must go inside twilio config to change.

ocbcbanking123@
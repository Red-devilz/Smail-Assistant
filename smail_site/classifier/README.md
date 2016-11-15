# Classification-Website Interface :


File List :
===========
* **api.py** : For API 
* **client\_secret.json** : Again for API 
* **website\_driver.py** : The website startup page that makes a call to the classifier(Website Side)
* **minified\_classifier.py** : The interface functions that will be provided from classifier side(Classifier side)
* **sample\_process.py** : An example function on how to process the return object the classifier sends(Website Side)

Website\_driver:
---------------
File makes an API call and get Gmail Auth details. Modify this as per requirements. Makes a call get_mails() function (in minified_classifier.py) that get the mails and class\_labels in the Mime Format.

Sample\_process:
---------------
Example file which contains sample\_print() function. Gives an example on how to process the received messages in Mime Format. For more understading of the return object check [here](https://developers.google.com/gmail/api/v1/reference/users/messages/get) and [here](https://developers.google.com/gmail/api/v1/reference/users/messages).

Minified\_classifier
------------------
Gets the Emails and classifies them using the get\_mails() function. Returns a list of Mail ID's, Mail Thread ID's , Mail body content(in Mime format) and Mail label.

How to Execute this ?
=====================
		cd classifier_sample
		python3 website_driver.py

Then run 127.0.0.1:8000 in the browser. This should then fetch Email contents and display it in the terminal.

Todo
====
* **Processing the Mime Object** : We have done very basic parsing that works for a few mails. Make sure to handle all kinds of mails, different languages(telugu, tamil mails). Also handle images and attachments which is not done by us. Also mails with formatting may have problems. Refer classifier branch to see some basic parsing done by us(we have ignored links, tables and email address etc.. so you cant use the exact same thing.)

* **GUI** work regarding mail display, labels display, using To,From and subject info.



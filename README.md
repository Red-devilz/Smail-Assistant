# Smail-Assistant

Fetch the data from your email
------------------------------
* To fetch data :
	  	
        cd source
        python3 data_aggregation.py
		
		Now open 127.0.0.1:800 in your browser to fetch all the data(and give credentials if required)


* Ensure that the required python packages are present. All the required packages are present in "source/requirements.txt". You can install the packages globally or run it in a virtualenvironment.

* If anyone does add more emails to "source/data" ensure that the naming scheme is changed to not overwrite the existing emails.

* To run the clustering algorithm :

        cd source
        python3 clustering.py

Cluster Category
----------------
0 : Seminars, Research Talks
1 : Sports
2 : Hostel Affairs
3 : Cultural/Literary affairs
4 : Academic - Courses
5 : Moodle
6 : research affairs
7 : General
8 : Ganga
9 : Misc.
10 : General Announcements
11 : iitm cse

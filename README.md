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

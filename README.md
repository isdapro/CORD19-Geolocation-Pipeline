# CORD19-Geolocation-Pipeline
Complete pipeline to automate affiliation scraping and geolocation

The requirements to run this program are:
1. Selenium and ChromeDriver
2. ElasticSearch setup on localhost:9200
3. Libpostal
4. Other requirements can be installed using requirements.txt
5. The links for pre-trained BERT Model and Cached Data Files

I understand that these are quite a lot of requirements and can complicate things for users looking for quick results. Thus,
I have provided a quick start Bash Script to load all of this into a Colab Notebook automatically and immediately get you going!

## Quick Start Instructions

1. Open a new notebook on Colab> Clone this repo and cd to the root directory
```
  !git clone https://github.com/isdapro/CORD19-Geolocation-Pipeline.git
  !cd CORD19-Geolocation-Pipeline/
```
2. Install the requirements by executing the bash Script. This may take a while..
```
  !bash ./load_stuff.sh
```
3. Now, download the latest metadata.csv from Kaggle (or the version you want to produce results for) and place it in the data directory of our project. You should see other files such as scraped.csv here, please don't modify them
```
/content/CORD19-Geolocation-Pipeline/geolocation-pipeline/data
```
4. Enter the main directory and execute the main python Script
```
!cd geolocation-pipeline
!python main.py
```

Here onwards, you can follow the instructions that you see on the screen. The script will allow you to choose to scrape, geolocate, change your API keys, etc.

#!/bin/bash

#Non Colab Setups especially VMs
#chromedriver
echo Installing ChromeDriver...
sudo apt-get update
sudo apt-get install chromium-chromedriver

#Set up elastic search on Colab
echo Setting up ElasticSearch on Localhost...
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.7.0-linux-x86_64.tar.gz -q
tar -xzf elasticsearch-7.7.0-linux-x86_64.tar.gz
elasticsearch-7.7.0/bin/elasticsearch -d

#May take some time for ES to load

#Set up libpostal
echo Setting up libpostal this could take a while...
sudo apt-get install curl autoconf automake libtool python-dev pkg-config
git clone https://github.com/openvenues/libpostal
cd libpostal
./bootstrap.sh
sudo mkdir /opt/libpostal
./configure --datadir=/opt/libpostal
make
sudo make install
sudo ldconfig
cd ..

echo Installing requirements...
pip install -r requirements.txt

#Fetching from GDrive
echo Getting the pre-trained BERT model...
cd geolocation-pipeline
wget --load-cookies /tmp/cookies.txt "https://drive.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://drive.google.com/uc?export=download&id=17s_hGrn1mTPDDi8XrARBxbQRwJXm32eZ' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=17s_hGrn1mTPDDi8XrARBxbQRwJXm32eZ" -O model_bert.zip && rm -rf /tmp/cookies.txt
unzip model_bert.zip

echo Fetching cached data...
wget --load-cookies /tmp/cookies.txt "https://drive.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://drive.google.com/uc?export=download&id=1kVRTilriKGfnfZ3CeveihyirT_r0tNED' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1kVRTilriKGfnfZ3CeveihyirT_r0tNED" -O data.zip && rm -rf /tmp/cookies.txt
unzip data.zip -d data/

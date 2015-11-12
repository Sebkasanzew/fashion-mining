# Zalando Textmining

## Installation instructions for Windows

### NLTK Installation
1. make sure python is installed
2. execute in the python command line <code>pip install nltk</code>
3. downloading nltk data by opening python and run:
```
>>> import nltk
>>> nltk.download()
```
4. select <code>C:/nltk_data</code> as the destination folder and select <code>download_all</code> in the list and then click on download
5. have fun

### GENSIM installation (no working guide yet)

---

## Installation instructions for Debian Linux (Ubuntu)

### NLTK Installation (Debian/Ubuntu Linux)
1. execute in the python command line <code>pip install nltk</code>
2. make sure in downloader.py line 380 in <code>/usr/local/lib/python2.7/dist-packages/nltk/</code> the <code>DEFAULT_URL</code> is set to <code>"http://nltk.github.com/nltk_data/"</code>
3. download nltk data by executing this command:
```
~$ sudo python -m nltk.downloader -d /usr/local/share/nltk_data all
```
4. have fun

### GENSIM installation

#### Dependencies

1. Python >= 2.7
2. NumPy >= 1.10
3. Scipy >= 0.16

#### Installation
open the terminal and execute the following code:
```bash
~$ sudo apt-get install libamd2.* libblas3gf libc6 libgcc1 \
libgfortran3 liblapack3gf libumfpack5.* libstdc++6 \
build-essential gfortran python-all-dev \
libatlas-base-dev 

~$ sudo apt-get install python-setuptools

~$ sudo easy_install pip

~$ pip install --upgrade gensim
(NumPy and SciPy would be downloaded automatically)
```

All dependencies should be resolved and installation is complete to use *GENSIM*
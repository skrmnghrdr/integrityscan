#!/usr/bin/python3
from os import path
from  Crawler import FileCrawler
from hashlib import file_digest


#3ntitities for ever I guess. 
#(. ) ( .)

class Hasher:
    """
    Usage:
    #from Hasher import Hasher
    #h = Hasher
    #h.hasheroo("abs_file_path")
    Hasher: takes in an absolute path, generates an md5sum for it

    Desc:
    Checks the file hash using md5sum.
    """
    def __init__(self):
        #pass an arguemnt to the function
        #instead of initializing an object 
        #for each file cause it's wayyy faster
        pass

    def hasheroo(self, absolute_path):
        with open(absolute_path, "rb") as f:
            hash_value = file_digest(f, "md5").hexdigest()
            #sketchy but with would clsoe the file as well after return
            return(hash_value)

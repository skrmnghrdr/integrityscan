#!/usr/bin/python3
import argparse
import json
from datetime import datetime
from os import path

#dependencies
from Hasher import Hasher
from Crawler import FileCrawler

"""
This script can be modded/used to see if any files had changed from a known good image of host.

May be also used to check changed files from a little directory

Use cases would be on a compromised host, you can  use this to verify the binaries that may have been changed if you have a copy or known good image of that system

How it works:
Simple file recursive crawler, crwals through the targeted directory and makes hashes of files.
On the suspected host, run the script with the good hashes to see if any of the files had changed

debating whether to put the absolute path of the binary

"""

def setup_parser():
    
    parser = argparse.ArgumentParser()
    #add menu

    parser.add_argument("--make-hash", "-m", action="store_true", default=False, help="Makes hashes of files in a target directory and stores them in a text file on CWD")
    parser.add_argument("--compare", "-c", action="store_true", default=False, help="Compares the hashes from a text file against a directory")

    #now to get arguments
    parser.add_argument("--dir", "-d",  type=str, help="The target directory. Default value: . (cwd)", default=".")
    parser.add_argument("--good-hash", "-g", type=str, help="Absolute path or relative path to the txtfile for known good hashes", default=None )

    now = datetime.now()
    default_output_name = now.strftime("hash_%Y-%m-%d%H:%M:%S.json")
    #sneak 100 so we get a fresh time
    parser.add_argument("--output", "-o", type=str, help="The filename of the hashoutput", default=default_output_name)

    return parser




def main():

    parser = setup_parser()
    args = parser.parse_args()

    #make sure the arguments are present.
    if args.make_hash ^ args.compare == False:
        parser.print_usage() 
        print("Need to select EITHER make OR Compare")
        return
    
    #then actually start processing things
    crawler = FileCrawler(args.dir)
    crawler.crawl()
    list_all_files = crawler.get_all_files()
    #print(all_folders)
    file_hash = {}
    hasher = Hasher()

    #could have put this in a function
    #start of hash table making
    for files in list_all_files:
        if args.make_hash == True:
            #just put the binary name in there
            filename = path.basename(files)
            print(filename)

            if filename in file_hash:
                iterator = 0
                new_filename = "{}_{}".format(filename, str(iterator))

                while new_filename in file_hash:
                    iterator += 1
                    new_filename = "{}_{}".format(filename, str(iterator))

                file_hash[new_filename] = hasher.hasheroo(files)
            else:
                file_hash[filename] = hasher.hasheroo(files)

        if args.compare == True:
            file_hash[files] = hasher.hasheroo(files)

    if args.make_hash == True:
        with open(args.output, 'w') as f:
            #dumps for further processing, dump for just makign a file
            json.dump(file_hash, f, indent=4)
            print("Saved good binary hashes as: {}".format(args.output))

    elif args.compare == True:
        if args.good_hash == None:
            print("ERROR: Good hash list empty, provide abs path")
            parser.print_usage()
            return
        
        #we have some good hash list then
        with open(args.good_hash, 'r') as f:
            good_file_hashes = json.load(f)
            #loads the json into a dictionary format
        
        hash_results = {
            "matched_good_bins": {},
            "possible_sus_bins": {},
            "unknown_bins": {},
            "descriptions": {
                "matchedGoodBins" : "They have matched the filenames and the hash",
                "possibleSusBins" : "Binaries that have matched one of the declared good binaries but have different filename",
                "unknownBins" : "Bins that did not match any of the good hashes"
            },
        }

        #meat and potatoes; let the for loop begin
        for key, value in file_hash.items():
            filename = path.basename(key)
            print("Searching for {} in good file hash: ".format(filename), end="")
            if filename in good_file_hashes:
                #use the key to compare the has
                if good_file_hashes[filename] == value:
                    #we have a legit one, then add it
                    print("GOOD!")
                    hash_results["matched_good_bins"][key] = value
                else:
                    #we might have a problem, same file name but not in good hash
                    print("SUSPICIOUS!!!")
                    hash_results["possible_sus_bins"][key] = value

            else:
                print("NO MATCH FOUND!!!")
                hash_results["unknown_bins"][key] = value
        with open(args.output, 'w') as f:
            json.dump(hash_results, f, indent=4)
            print("Saved scan results as: {}".format(args.output))
        



         
        #compare args here
    else:
        #shieeee if you even make it here on the flow
        #I don't even know how
        parser.print_usage()
        return

    #automatically converts - to underscore sooo
    #args.dir 
    #args.goodhash

    """

crawler = FileCrawler('.')
crawler.crawl()
hasher = Hasher()
hasher.hasheroo()
file_list = crawler.get_all_files()
for things in file_list:
    with open(things, "rb") as f:
        #uncomment to show verbose below
        #print("Filename: {} Hash: {} ".format(path.basename(things), file_digest(f, "md5").hexdigest(), end="") )
    
        

def hash_maker(args):
    #make sure to put filenames here
    #to avoid binary duplication.
    #which can be very dangerous
    
    crawler = FileCrawler(args.dir)
    crawler.crawl()
    list_all_files = crawler.get_all_files()
    #print(all_folders)
    file_hash = {}
    hasher = Hasher()
    for files in list_all_files:
        file_hash[files] = hasher.hasheroo(files)

    if args.make_hash == True:
    #with open(args.output, 'w') as f:
        #dumps for further processing, dump for just makign a file
        json.dump(file_hash, f, indent=4)
        print("Saved good binary hashes as: {}".format(args.output))
        #hashes.append(hasher.hasheroo(files))
    #just for debugging 
    #print(json.dumps(file_hash, indent=4))
    """
main()
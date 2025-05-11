import os

class FileCrawler:
    """
    Usage: 
    from Crawler import FileCrawler
    crawler = FileCrawler('.')
    crawler.crawl()

    Takes in a path and it will crawl recursively on that

    """
    def __init__(self, root_path):
        self.root_path = root_path
        self.all_files = []
        self.all_folders = []

    def crawl(self):
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Add directories
            for dirname in dirnames:
                full_dir = os.path.join(dirpath, dirname)
                self.all_folders.append(full_dir)
            # Add files
            for filename in filenames:
                full_file = os.path.join(dirpath, filename)
                self.all_files.append(full_file)

    def get_all_files(self):
        #returns a list (array)
        return self.all_files

    def get_all_folders(self):
        #returns a list (array)
        return self.all_folders
    #might be useful later, 
    def get_files_by_extension(self, extension):
        return [f for f in self.all_files if f.endswith(extension)]

    """
    path = "/home/user/documents/myfile.txt"
    filename = os.path.basename(path)
    #to extract the basename (filename of the path)
    """

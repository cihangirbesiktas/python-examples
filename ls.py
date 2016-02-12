#!/usr/bin/python
# coding=utf-8

"""an implementation of ls command for the following command line arguments

-l : list in long format
-h : human readable format
-S : sort files by file size
-a : view hidden files
-F : append indicator / to directories

on illegal parameter the following output is given:
ls: illegal option -- <param>
usage: ls [-lhSaF] [file ...]
"""

import sys, getopt, os, pwd, grp, stat
import time
from time import strftime

class File(object):
    """
     Class for holding and returning file attributes like name, stat, type,
     access time, size in int, string and human readable form, number of hardlinks,
     username, groupname and permissions
    """
    def __init__(self, name, directory):
        self.name = name
        self.directory = directory
        self.stat = self.get_stat()
        self.type = self.get_type()

    def get_name(self):
        return self.name

    def get_stat(self):
        try:
            return os.stat(self.directory + self.name)
        except os.error as e:
            print e.message

    def get_type(self):
        if stat.S_ISDIR(self.stat.st_mode):
            return "d"
        elif stat.S_ISLNK(self.stat.st_mode):
            return "l"
        elif is_symlink(self.directory + self.name):
            return "l"
        elif stat.S_ISREG(self.stat.st_mode):
            return "-" 
        elif stat.S_ISBLK(self.stat.st_mode):
            return "b" 
        elif stat.S_ISCHR(self.stat.st_mode):
            return "c" 
        elif stat.S_ISFIFO(self.stat.st_mode):
            return "p"
        elif stat.S_ISSOCK(self.stat.st_mode):
            return "s"
        else:
            return "?"

    def get_time(self):
        aTime = time.localtime(self.stat.st_atime)
        curYear = time.localtime().tm_year
        if aTime.tm_year < curYear - 1:
            return strftime("%b %d %H:%M", aTime)
        else:
            return strftime("%b %d %Y", aTime)

    def get_size_str(self):
        return str(self.stat.st_size)

    def get_size(self):
        return self.stat.st_size

    def get_human_readable_size(self):
        size = self.stat.st_size
        KB = 1024
        MB = KB * 1024
        GB = MB * 1024
        TB = GB * 1024
        if size < KB:
            return str(size)
        elif size < MB:
            return str(size/KB) + "K"
        elif size < GB:
            return str(size/MB) + "M"
        elif size < TB:
            return str(size/GB) + "G"
        else:
            return str(size/TB) + "T"

    def get_link_count(self):
        return str(self.stat.st_nlink)

    def get_user_name(self):
        try:
            return pwd.getpwuid(self.stat.st_uid).pw_name
        except KeyError as e:
            print e.message

    def get_group_name(self):
        try:
            return grp.getgrgid(self.stat.st_gid).gr_name
        except KeyError as e:
            print e.message
 
    def get_permissions_text(self):
        if self.type == "l":
            return "lrwxrwxrwx"
        rwxList = ["---", "--x", "-w-", "-wx", "r--", "r-x", "rw-", "rwx"]
        ownPerms = rwxList[(self.stat.st_mode >> 6) & 7]
        grpPerms =   rwxList[(self.stat.st_mode >> 3) & 7]
        othPerms = rwxList[(self.stat.st_mode) & 7]
        if self.stat.st_mode & stat.S_ISUID:
            if self.stat.st_mode & stat.S_IXUSR:
                ownPerms = ownPerms[:2] + "s"
            else:
                ownPerms = ownPerms[:2] + "S"
        if self.stat.st_mode & stat.S_ISGID:
            if self.stat.st_mode & stat.S_IXGRP:
                grpPerms = grpPerms[:2] + "s"
            else:
                grpPerms = grpPerms[:2] + "S"
        if self.stat.st_mode & stat.S_ISVTX:
            if self.stat.st_mode & stat.S_IXOTH:
                othPerms = othPerms[:2] + "t"
            else:
                othPerms = othPerms[:2] + "T"
        return self.get_type() + ownPerms + grpPerms + othPerms

class FileList(object):
    """
    List handler for File instances. Holds File instances and performs functionalities of the ls command with
     the given parameters in <options> dictionary variable.

    When initialized, holds empty list. The function add_files_from_path can be used to add files in a directory.
    The function add_file can be used to add a specific file.
    """
    def __init__(self, options=None):
        """
        x.__init__(...) initializes x; see help(type(x)) for more information
        :param options: dictionary which holds arguments of ls command
        """
        self.files = []
        if options is None:
            self.options = {"a": False, "F": False, "h": False, "l": False, "S": False}
        else:
            self.options = options
        self.maxFileSize = 0
        self.maxUserNameSize = 0
        self.maxGrpNameSize = 0
        self.maxHarLinkSize = 0

    def add_files_from_path(self, path):
        """
        Adds files of the given directory to the list including . and .. files
        :param path: directory name
        """
        if path[-1] != "/":
            path = path + "/"

        fileNames = list_dir(path)
        fileNames.append(".")
        fileNames.append("..")
        for item in fileNames:
            if item[0] == "." and not self.options['a']:
                continue
            else:
                self.files.append(File(item, path))
        self.set_maximums()
        self.sort_file_list_by_name()

    def add_file(self, path, name):
        """
        Adds the file specified with the given directory and file name
        :param path: directory name
        :param name: file name
        """
        if path[-1] != "/":
            path = path + "/"
        self.files.append(File(name, path))
        self.set_maximums()
        self.sort_file_list_by_name()

    def set_maximums(self):
        """
        Sets the maximum string lengths of some dynamic fields for ls long list format
          These fields are file size, username, groupname, hard link size.
        """
        self.set_max_file_size()
        self.set_max_user_name_size()
        self.set_max_group_name_size()
        self.set_max_hard_link_size()

    def set_max_file_size(self):
        max = 0
        for file in self.files:
            if len(file.get_size_str()) > max:
                max = len(file.get_size_str())
        self.maxFileSize = max

    def set_max_user_name_size(self):
        max = 0
        for file in self.files:
            if len(file.get_user_name()) > max:
                max = len(file.get_user_name())
        self.maxUserNameSize = max

    def set_max_group_name_size(self):
        max = 0
        for file in self.files:
            if len(file.get_group_name()) > max:
                max = len(file.get_group_name())
        self.maxGroupNameSize = max

    def set_max_hard_link_size(self):
        max = 0
        for file in self.files:
            if len(file.get_link_count()) > max:
                max = len(file.get_link_count())
        self.maxHarLinkSize = max

    def set_options(self, options):
        """
        Updates dictionary variable options which is for ls command arguments
        :param options: dictionary which holds arguments of ls command
        """
        self.options = options

    def get_file_name(self, file):
        """
        Returns the file name according to command line arguments given in options.
        F argument is for appending / to the end of the name
        If the file is a symbolic link, then the special output of it is returned.
        :param file: File object
        :return: file name as string
        """
        fileName = file.name
        if self.options["F"] and file.get_type() == "d":
            fileName = fileName + "/"
        if file.get_type() == "l" and self.options["l"]:
            try:
                fileName = fileName + " -> " + os.readlink(file.directory + file.name)
            except OSError as e:
                print e.message
        return fileName

    def get_normal_format(self, file):
        """
        Returns the filename for normal file listing
        :param file: File object
        :return: file name as string
        """
        return self.get_file_name(file)

    def get_long_listing_format(self, file):
        """
        Returns the filename for long listing format
        :param file: File object
        :return: long listing format of the file as string
        """
        if self.options["h"]:
            fileSize = file.get_human_readable_size()
        else:
            fileSize = file.get_size_str()
        fileSize = get_space_chars(self.maxFileSize - len(fileSize)) + fileSize
        userName = file.get_user_name() + get_space_chars(self.maxUserNameSize - len(file.get_user_name()))
        groupName = file.get_group_name() + get_space_chars(self.maxGroupNameSize - len(file.get_group_name()))
        hardLinkSize = get_space_chars(self.maxHarLinkSize - len(file.get_link_count())) + file.get_link_count()
        return file.get_permissions_text() + " " + hardLinkSize + " " + userName + " " + groupName + " " + fileSize + " " + file.get_time() + " " + self.get_file_name(file)

    def get_file_info(self, file):
        """
        Gets a file's listing based on its :l: parameter
        :param file: File object
        :return: file's listing as string
        """
        if self.options["l"]:
            return self.get_long_listing_format(file)
        else:
            return self.get_normal_format(file)

    def sort_file_list_by_size(self):
        """
        Sorts the file list according to sizes of files.
        """
        self.files.sort(key=lambda x: x.get_size(), reverse=True)

    def sort_file_list_by_name(self):
        """
        Sorts the file list according to names of files.
        """
        self.files.sort(key=lambda  x: x.name, reverse=False)

    def show(self):
        """
        Shows listing of all the files based on the given arguments
        """
        if self.options["S"]:
            self.sort_file_list_by_size()

        output = ""
        for file in self.files:
            if self.options["l"]:
                output = output + self.get_long_listing_format(file) + "\n"
            else:
                output = output + self.get_normal_format(file) + "\t"
        print(output[:-1])


def print_no_such_file_or_dir_error(noFileOrDirList):
    """
    Prints ls' error info for arguments that does not exist on the specified location
    :param noFileOrDirList: List holding files or directories that is not in the system
    """
    for item in noFileOrDirList:
        print("ls: " + item +": No such file or directory")
    usage()

def is_symlink(path):
    """
    Returns True when the path is a symbolic links, otherwise False
    :param path: pathname of a file
    """
    try:
        return os.path.islink(path)
    except os.error as e:
        print e.message

def list_dir(path):
    """
    Returns filenames in a path as link
    :param path: directory path
    """
    try:
        return os.listdir(path)
    except os.error as e:
        print e.message

def get_dir_name(path):
    """
    Returns the directory name of a files path
    :param path: file path
    """
    try:
        return os.path.dirname(path)
    except os.error as e:
        print e.message

def get_cwd():
    """
    Returns current working directory
    """
    try:
        return os.getcwd()
    except os.error as e:
        print e.message

def get_space_chars(numSpaces):
    """
    Returns a string having numSpaces times space.
    :param numSpaces: number of space
    """
    space = ""
    if numSpaces < 1:
        return space
    for i in range(numSpaces):
        space = space + " "
    return space

def usage():
    """
    Prints usage of the implemented ls command
    """
    print("usage: ls [-aFhlS] [file ...]")

def print_illegal_option(illegalOption):
    """
    Print function for illegal arguments
    :param illegalOption: argument name of the illegal option
    """
    print("ls: illegal option -- " + illegalOption)


def output_of_no_args(options):
    """
    Shows results for when there is no file name of directory name is given as argument
    """
    files = FileList(options)
    files.add_files_from_path(get_cwd())
    files.show()

def output_of_file_args(fileArgs, options):
    """
    Shows results for the given file arguments
    """
    files = FileList(options)
    for file in fileArgs:
        path = get_dir_name(file)
        if path == "":
            path = get_cwd()
        files.add_file(path, file)
    files.show()

def output_of_dir_args(dirArgs, argcnt, options):
    """
    Shows results for the given directory arguments
    """
    cnt = 0
    for dir in dirArgs:
        dirFiles = FileList(options)
        dirFiles.add_files_from_path(dir)
        if argcnt > 1:
            print(dir + ":")
        dirFiles.show()
        cnt += 1
        if cnt < len(dirArgs):
            print("")

def main(argv):
    """
    Main funtion for the implemented ls command
    """
    # Default options
    dictOpts = {"a": False, "F": False, "h": False, "l": False, "S": False}

    # options given from the command line is set to True
    try:
        opts, args = getopt.getopt(argv,"aFhlS",[])
    except getopt.GetoptError as e:    	
        print_illegal_option(e.opt)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-a':
            dictOpts["a"] = True
        elif opt == '-F':
            dictOpts["F"] = True
        elif opt == '-h':
            dictOpts["h"] = True
        elif opt == '-l':
            dictOpts["l"] = True
        elif opt == '-S':
            dictOpts["S"] = True

    # lists for files, directories and names that is not file or directory
    fileArgs = []
    dirArgs = []
    noFileOrDirArgs = []

    # if no argument is given then print the file infos of the current working directory with given options
    if len(args) == 0:
        output_of_no_args(dictOpts)
    # print the file infos of the given filenames and directories
    else:
        for arg in args:
            if os.path.isfile(arg):
                fileArgs.append(arg)
            elif os.path.isdir(arg):
                dirArgs.append(arg)
            else:
                noFileOrDirArgs.append(arg)

        if len(noFileOrDirArgs) > 0:
            print_no_such_file_or_dir_error(noFileOrDirArgs)
        if len(fileArgs) > 0:
            output_of_file_args(fileArgs, dictOpts)
        if len(dirArgs) > 0:
            output_of_dir_args(dirArgs, len(fileArgs) + len(dirArgs), dictOpts)

if __name__ == "__main__":
   main(sys.argv[1:])

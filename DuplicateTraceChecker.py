import os
from tkinter import *
from tkinter.filedialog import *
import numpy as np

def checkDuplicateTraces(traces):
    """For a list of traces under the same object name and section, return indices of duplicates after first instance"""
    
    # store the index of duplicate traces
    duplicates = []
    
    for i in range(len(traces)):
        # skip traces that were already found to be duplicates
        if not i in duplicates:
            for j in range(i+1, len(traces)):
                if traces[j] == traces[i]:
                    # if traces have the same list of coords, label it as a duplicate
                    duplicates.append(j)
    
    return duplicates           



def loadTraces(fileName):
    """Load all of the traces in a single section file to a dictionary (key = name : value = nested list)"""
    
    # create dictionary
    allTraces = {}
    
    # open, read, and close section file
    sectionFile = open(fileName, 'r')
    lines = sectionFile.readlines()
    sectionFile.close()
    
    # recording: set to True whenever the points in the file are being recorded
    recording = False    
    
    # iterate through section file
    for lineIndex in range(len(lines)):
        line = lines[lineIndex]
        
        if recording:
            # the first point starts with "points=" in the text file; remove this
            if firstLine:
                line = line.replace('points="', '')
                firstLine = False
            
            #remove commas
            line = line.replace(',', '')
            
            coords = line.split()
            
            # check if there are still points there, stop recording otherwise
            if len(coords) == 2:
                point = [[float(coords[0])],[float(coords[1])],[1]]
                point = np.matmul(transformation, point)
                trace.append(round(point[0][0],3))
                trace.append(round(point[1][0],3))
            else:
                recording = False
                
                # when finished recording, add trace coords to allTraces dictionary
                
                # append to existing list of object has already been found
                if objName in allTraces:
                    allTraces[objName].append(trace)
                    
                # if first instance of object, create a new list for the key in the dictionary
                else:
                    allTraces[objName] = [trace]
                    
        else:
            # check for object name in the line
            if '<Contour name="' in line:
                recording = True
                firstLine = True
                objName = line.split('"')[1]
                trace = []
                
                # grab the transformation
                trans_i = lineIndex
                while not "xcoef=" in lines[trans_i]:
                    trans_i -= 1
                xcoef = [float(x) for x in lines[trans_i].split()[1:4]]
                ycoef = [float(y) for y in lines[trans_i+1].split()[1:4]]
                transformation = coefToTransformation(xcoef, ycoef)

                
    
    return allTraces

def coefToTransformation(xcoef, ycoef):
    """Return transformation data based on the xcoef and ycoef"""
    return np.linalg.inv(np.array([[xcoef[1], xcoef[2], xcoef[0]],
                   [ycoef[1], ycoef[2], ycoef[0]],
                   [0, 0, 1]]))



def removeDuplicates(fileLocation, newLocation, duplicates):
    """Scan through a section file and remove duplicate traces"""
    
    # open, read, and close section file
    sectionFile = open(fileLocation, "r")
    lines = sectionFile.readlines()
    sectionFile.close()
    
    # iterate through the section file for every duplicate object found
    for obj in duplicates:
        # count instances of the object in the file
        counter = -1
        
        # keep track of when deleting is occuring
        deleting = False
        
        # iterate through the section file
        for i in range(len(lines)):
            
            line = lines[i]
            
            # if the iterator comes across the object of interest...
            if ('"' + obj + '"') in line:
                # keep track of how many times the object has appeared
                counter += 1
                
                # if the counter matches a duplicate trace index...
                if counter in duplicates[obj]:
                    #start deleting by replacing the line with an empty string
                    deleting = True                    
                    lines[i] = ""
                    
                    # check if the trace is on its own or within a group of traces
                    grouped = False
                    
                    # "/> right before obj name indicates a grouped trace
                    if '"/>' in lines[i-1]:
                        grouped = True
                    
                    # iterate forwards to find when the trace ends
                    j = i
                    while not '"/>' in lines[j]:
                        j += 1
                    # </Transform> donates end of block; if not found, then the trace is grouped
                    if not '</Transform>' in lines[j+1]:
                        grouped = True
                    
                    # if trace is not grouped, remove the previous four lines
                    if not grouped:
                        for j in range(1,5):
                            lines[i-j] = ""

            elif deleting:
                lines[i] = ""
                
                # if grouped, stop at "\>
                if '"/>' in line and grouped:
                    deleting = False
                # if ungrouped, stop deleting at </Transform>
                elif "</Transform>" in line:
                    deleting = False

    # write modified lines to a new file; skip empty strings
    newFile = open(newLocation, "w")
    for line in lines:
        if line:
            newFile.write(line)



def formatNumberList(numList):
    """Format a list of numbers so that it prints out in a readable format"""
    
    # create a list of pairs of numbers (start and end of hyphenation)
    formattedList = []
    
    # keep track of first and last number in list of adjacent numbers
    start = numList[0]
    
    # iterate through numlist (except for last object)
    for i in range(len(numList)-1):
        
        #if the next term isn't adjacent...
        if numList[i+1] != numList[i] + 1:
            
            # add [start, end] pair to formattedList
            end = numList[i]
            formattedList.append([start, end])
            
            # set a new starting number
            start = numList[i+1]
            
    # make the last object the end and add the final pair to formattedList
    end = numList[len(numList)-1]
    formattedList.append([start, end])
    
    # turn the formatted list into a string
    outputStr = ""
    
    for i in range(len(formattedList)):
        pair = formattedList[i]
        
        # if the list is at the last object, don't add a comma to the end
        if i == len(formattedList)-1:
            comma = ""
        # otherwise, add a comma to the end
        else:
            comma = ", "
        
        # if the number is alone, add just the number 
        if pair[0] == pair[1]:
            outputStr += str(pair[0]) + comma
        # otherwise, add the hyphenated pair
        else:
            outputStr += str(pair[0]) + "-" + str(pair[1]) + comma
    
    return outputStr   



def getSeriesInfo(fileName):
    """Return the series name and number of sections."""

    # get only the name
    series_name = fileName[fileName.rfind("/")+1:fileName.rfind(".")]
    file_path = fileName[:fileName.rfind("/")+1]
    os.chdir(file_path)
    
    # find out how many sections there are
    section_nums = []
    
    # search each file in the folder that ends with a number
    for file in os.listdir():
        try:
            section_nums.append(int(file[file.rfind(".")+1:]))
        except:
            pass

    # sort the section numbers so they are in order
    section_nums.sort()

    return series_name, file_path, section_nums


# BEGINNING OF MAIN

try:
    print("Please locate the series file that you wish to check for trace duplicates.")
    input("Press enter to open your file browser.")

    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    fileName = askopenfilename(title="Open a Series File",
                               filetypes=(("Series File", "*.ser"),
                                          ("All Files","*.*")))

    if not fileName:
        raise Exception("No series file was selected.")
    
    print("\nRetrieving series info...")
    series, location, section_nums = getSeriesInfo(fileName)
    
    print("\nFinding duplicates for " + series + " across " + str(len(section_nums)) + " sections...")
    print("This may take a few minutes.")



    # record every duplicate on every section
    # this will be a list of dictionaries, with each dictionary representing the duplicates on a single section
    # dictionary format: key = object name, value = list of indices where object is duplicated
    masterList = []

    # keep track of which objects are duplicated on which sections
    objectsDuplicated = {}

    # iterate through all section files
    for i in section_nums:
        
        # load all the traces from a single section into a dictionary
        allTraces = loadTraces(series + "." + str(i))
        
        # store duplicate object instances on this section in dictionary
        allDuplicates = {}
        
        # interate through each object in allTraces and check for duplicates
        for obj in allTraces:
            duplicates = checkDuplicateTraces(allTraces[obj])
            
            # if there are duplicates on this section for the given object, add it to the allDuplicates dictionary
            if len(duplicates) > 0:
                allDuplicates[obj] = duplicates
        
        # after iterating through all objects on the section, check for any duplicate objects
        for obj in allDuplicates:
            
            # add duplicate objects to dictionary and record section number
            if obj in objectsDuplicated:
                objectsDuplicated[obj].append(i)
            else:
                objectsDuplicated[obj] = [i]
        
        # add allDuplicates dictionary to masterList
        masterList.append(allDuplicates)

    # print duplicated objects
    objects = list(objectsDuplicated.keys())
    objects.sort()

    if len(objectsDuplicated) == 0:
        print("\nThere are no duplicated objects.")
    else:
        print()
        for obj in objects:
            print(obj + " is duplicated on section(s): " + formatNumberList(objectsDuplicated[obj]))

        # prompt for duplicates removal
        remove = input("\nWould you like to remove these duplicates? (y/n): ")

        if remove == "y":

            # get a new file location, make sure its different from the old one
            newLocation = location
            while newLocation == location:
                print("\nPlease locate an empty folder to contain the new series.")
                input("Press enter to open your file browser.")
                newLocation = askdirectory()
                if not newLocation:
                    raise Exception("No folder selected.")

            # remove the duplicate traces and write new files
            print("\nRemoving duplicate traces...")
            for i in section_nums:
                removeDuplicates(location + "\\" + series + "." + str(i),
                                 newLocation + "\\" + series + "." + str(i),
                                 masterList[i])

            # copy over exact same series file
            print("\nCopying original series file...")

            oldSeriesFile = open(location + "\\" + series + ".ser", "r")
            newSeriesFile = open(newLocation + "\\" + series + ".ser", "w")

            for line in oldSeriesFile.readlines():
                newSeriesFile.write(line + "\n")

            oldSeriesFile.close()
            newSeriesFile.close()


            print("\nCompleted!")

except Exception as e:
    print("ERROR: " + str(e))

input("\nPress enter to exit.")

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
                trace.append(round(float(coords[0]), 3))
                trace.append(round(float(coords[1]), 3))
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
    
    return allTraces



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


try:
    series = input("What is the name of the series?: ")
    num = int(input("How many sections are in this series?: "))
    location = input("What is the folder directory for the series?: ")



    # record every duplicate on every section
    # this will be a list of dictionaries, with each dictionary representing the duplicates on a single section
    # dictionary format: key = object name, value = list of indices where object is duplicated
    masterList = []

    # keep track of which objects are duplicated on which sections
    objectsDuplicated = {}

    # iterate through all section files
    for i in range(num):
        
        # load all the traces from a single section into a dictionary
        allTraces = loadTraces(location + "\\" + series + "." + str(i))
        
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
        print("There are no duplicated objects.")
    else:
        for obj in objects:
            print(obj + " is duplicated on section(s) " + formatNumberList(objectsDuplicated[obj]))

        # prompt for duplicates removal
        remove = input("Would you like to remove these duplicates? (y/n): ")

        if remove == "y":

            # get a new file location, make sure its different from the old one
            newLocation = input("What is the directory for the empty folder?: ")
            while newLocation == location:
                print("Old and new file paths cannot be the same.")
                newLocation = input("What is the directory for the empty folder?: ")

            # remove the duplicate traces and write new files
            print("Removing duplicate traces...")
            for i in range(num):
                removeDuplicates(location + "\\" + series + "." + str(i),
                                 newLocation + "\\" + series + "." + str(i),
                                 masterList[i])

            # copy over exact same series file
            print("Copying original series file...")

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

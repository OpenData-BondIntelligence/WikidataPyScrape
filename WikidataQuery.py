import googlemaps
import re
import pandas as pd
import geopy as geo
from geopy.geocoders import Nominatim
from StateIDS import STATE_IDS
from StateStrings import STATE_NAMES
from SPARQLWrapper import SPARQLWrapper, JSON, XML

def main():
    #Variable to store whether we need to query Google maps API
    needToQuery = None
    #Variable to store the output of the Google maps API query
    reverseGeoCodeOut = None
    #authenticate google API key
    gmaps = googlemaps.Client(key='AIzaSyDjA5nLQv9wHwC84868FN26y0POzA95HWA')
    #declare the output CSV file
    filePath = open("pyOutput.csv", "w", encoding='utf-8')
    #declare where SPARQL queries will be fed to
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    #set return format as JSON for SPARQLWrapper. The JSON is seperated by commas by my hardcoded formatting, 
    #so we can simply rename the output file to CSV rather than JSON
    sparql.setReturnFormat(JSON)

    #write the collumn labels for the CSV file
    filePath.write("State,County,Website,Population,Coordinates,Wikidata ID\n")
    #largest for loop to iterate through all IDS found in STATE_IDS and write SPARQL output in output file
    for stateID in STATE_IDS:
        #define the SPARQL query to send to WikiData
        sparql.setQuery("""
            SELECT ?item ?itemLabel ?stateLabel ?website ?population ?coordinates
            WHERE
            {
                ?item wdt:P31 wd:%s;
                wdt:P131 ?state;
                wdt:P1082 ?population;
                wdt:P856 ?website;
                wdt:P625 ?coordinates.
                SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
            }
            ORDER BY DESC(?population)
        """ %stateID)
        #honestly not sure what this does I believe it makes it into a 2d array
        results = sparql.query().convert()

        #for loop to go through all results from each SPARQL query
        for result in results["results"]["bindings"]:
            #Reset our needToQuery variable declared above
            needToQuery = True

            #next block of lines is formatting text to look good and function in the CSV
            State = result["stateLabel"]["value"].replace(",","")
            County =  result["itemLabel"]["value"].replace(",","")
            Website =  result["website"]["value"].replace(",","")
            Population = result["population"]["value"].replace(",","")
            Coordinates = result["coordinates"]["value"].replace(",","")
            wikiID = result["item"]["value"].split("/")
            

            if County == "Fremont":
                print("Fremont found")

            #formatting the WikiData coordinate output to work with Google maps API
            #pulls out only the digits from the string given by WikiData and assigns to two
            #seperate variables
            formatCoordinates = re.findall(r"-?\d+\.?\d*", Coordinates)
            Longitude = formatCoordinates[0]
            Latitude = formatCoordinates[1]

            #DEBUG STATEMENT
            #print(State)

            for stateName in STATE_NAMES:
                if State == stateName:
                    
                    #DEBUG STATEMENT
                    #print (State, stateName)
                    needToQuery = False
                    break

            #query Google maps API with a coordinate pair to get various location data
            if needToQuery:
                reverseGeoCodeOut = gmaps.reverse_geocode((Latitude, Longitude))

            #enter statement if coordinate pair search gave an output
            if reverseGeoCodeOut:
                for x in reverseGeoCodeOut[0]["address_components"]:
                    #iterate through list until we find the state section
                    if "administrative_area_level_1" in x["types"]:
                        State = x["long_name"]

                        #DEBUG STATEMENT
                        #print(State)

                        #no need to continue after state has been found
                        break
            #DEBUG STATEMENT        
            #else:
                #catch statement in case NULL result from Google API
                #currently the str assignment line is commented because our results will be REPLACING
                #the entries for state rather than going in a new collumn
                #State = "Reverse Geocode search either not executed or failed"
                
                
                #print(State)

            #write all output into the CSV file
            filePath.write(State + "," +
                        County + "," +
                        Website + "," +
                        Population + "," +
                        Coordinates + "," +
                        wikiID[-1] + "\n")
    filePath.close()

    #remove duplicate website entries from the output CSV, creating a new CSV with no duplicate entries
    dupeFile = pd.read_csv("pyOutput.csv", sep = ",", error_bad_lines = False)
    #dupeFile.drop_duplicates(subset = "Wikidata ID", inplace = False)
    dupeFile = dupeFile.drop_duplicates(subset = 'Wikidata ID', keep = 'first', inplace = False)
    dupeFile.to_csv("pyOutputNoDuplicates.csv")

if __name__ == "__main__":
    main()
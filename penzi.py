from flask import Flask, request, jsonify
import mysql.connector
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
conn = mysql.connector.connect(host='mysql',
                               database='mpenzi',
                               user='root',
                               password='#Matsukah254',
                               auth_plugin ='caching_sha2_password'
                               )





@app.route('/api', methods=['POST'])  
def fetch_det():
    req = request.get_json()
    msisdn = req.get("from")
    message =req.get("body")
    ack = req.get("ack")

    if ack == 1 and msisdn.endswith("@c.us"):
        Msisdn = msisdn.split("@")
        mSisdn = Msisdn[0]
        msisdn = f"+{mSisdn}"
        store_messages(msisdn, message)
        respons = handle_message(msisdn, message)
        print(respons)
        store_outgoing_messages(msisdn,respons)
        return jsonify({"reply":respons})
    
def handle_message(msisdn,message):
    
    
    if message.lower() == "penzi": 

        response = "Welcome to our dating service with 6000 potential dating partners! To register SMS start#name#age#gender#county#town to 22141. E.g., start#John Doe#26#Male#Nakuru#Naivasha"
        return response

    elif len(message) ==13 :
            fetch_msisdn_details(msisdn)

            msisdn = normalize_msisdn(message)
        
            query = "SELECT name, age, county, town, level_of_education, profession, marital_status, religion, ethnicity FROM users WHERE msisdn = %s"
            cursor = conn.cursor()
            cursor.execute(query, (msisdn,))
            results = cursor.fetchone()
            cursor.close()

            if results is None:
                response = f"Phone number {msisdn} does not exist."
            else:
                name, age, county, town, level_of_education, profession, marital_status, religion, ethnicity = results
                text = f"{name} aged {age} county {county} town {town} level of education {level_of_education} profession {profession} marital status {marital_status} religion {religion} ethnicity {ethnicity}"               
                more_text = f"Send DESCRIBE#{msisdn} to get more details"
                response = text + more_text     
                            
            return response
               
            
    else:
        return split_message(message, msisdn)
    
def split_message(message,msisdn):
    message = message.split("#")
    keyword = message[0]
    content = message[1:]

    if keyword.lower() == "start":
        contents = split_content(content)
        if contents is None:
            return "The content does not have enough elements"
        
        name = contents["name"]
        age = contents["age"]
        gender = contents["gender"]
        county = contents["county"]
        town = contents["town"]
        
        response = check_name_age_gender(name, age, gender, county, town)

        if response is not None:
            return response

        if check_details(msisdn):
                text = "You were registered for dating with your initial details. To search for a MPENZI, SMS match#age#town to 22141 and meet the person of your dreams.E.g., match#23-25#Nairobi"
                return text
        else:
                name, age, gender, county, town =content
                query = ("INSERT INTO users (msisdn,name,age,gender,county,town)"
                        "VALUES(%s, %s,%s, %s,%s,%s)")
        
        cursor =conn.cursor()
        cursor.execute(query,(msisdn,name,age,gender,county,town,))
        conn.commit()
        cursor.close()
        
        text = f"Your profile has been created successfully {name}. SMSdetails#educationlevel#profession#maritalStatus#religion#ethnicity to 22141. E.g. details#diploma#driver#single#christian#mijikenda"
        return text
    
        

    elif keyword.lower() == "details":
        contents = split_details(content)
        if contents is None:
            return "The content does not have enough elements"
        

        level_of_education = contents["level_of_education"]
        profession = contents["profession"]
        marital_status = contents["marital_status"]
        religion = contents["religion"]
        ethnicity = contents["ethnicity"]

        response = check_details_content(level_of_education, profession, marital_status, religion, ethnicity)

        if response is not None:
            return response
        
        level_of_education, profession, marital_status, religion, ethnicity =content
        usr_id =getuser_id(msisdn)
        query = ("UPDATE users ""SET level_of_education = %s, profession = %s, marital_status = %s, religion = %s, ethnicity = %s "
         "WHERE user_id = %s")
        

        cursor =conn.cursor()
        cursor.execute(query,(level_of_education,profession,marital_status,religion,ethnicity,usr_id))
        conn.commit()
        cursor.close()   
        text = "This is the last stage of registration. SMS a brief description of yourself to 22141 starting with the word MYSELF. E.g., MYSELF#chocolate, lovely, sexy etc"
        return text


    elif keyword.lower() == "myself":
        description = content[0]
        usr_id = getuser_id(msisdn)
        query = "UPDATE users SET description = %s WHERE user_id = %s"
        cursor = conn.cursor()
        cursor.execute(query, (description, usr_id))
        conn.commit()
        cursor.close()
            
        text = "You are now registered for dating.To search for a MPENZI, SMS match#age#town to 22141 and meet the person of your dreams.E.g., match#23-25#Kisumu"
        return text
    

    elif keyword.lower() =="match":
        age, town = content
        results,row_count = match(age, town, msisdn)
        if results:
            display_results = displayfirstthree(results) 
            delete_first_three(results)
            reply = f"We have {row_count} ladies who match your choice!Here are details of 3 of them.To get more details about a lady, SMS her number e.g., 0722010203 to 22141"
            text = "Send NEXT to 22141 to receive details of the remaining  ladies"
            
            response = reply, display_results, text          
            
            return  response
        else:
            return "no result found for your selected catagory"
    
    elif keyword.lower() =="describe":
        msisdn = content[0]
        normalized_msisdn = normalize_msisdn(msisdn)
        query = "SELECT description FROM users where msisdn = %s"
        cursor = conn.cursor()
        cursor.execute(query, (normalized_msisdn, ))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        text = f"Describes herself as {result} and will make you tick"
        return text if result else "No description for the given msisdn"
    
    elif message[0].lower() =="next":  
               
        query = "SELECT name, msisdn FROM matches LIMIT 3"
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.commit()
        cursor.close()

        more_text = "To view the next three results, send Next"
        
        extracted_results = []
        for result in results:
            name, msisdn = result
            extracted_results.append(f"Name: {name}, Phone num: {msisdn}")

        response = more_text + "\n" + "\n".join(extracted_results)
        
        delete_first_three(results)

        return response

    elif message[0].lower() =="yes":
        incoming_message = msisdn
        query = "SELECT msisdn FROM messages WHERE incoming_message = %s"
        cursor = conn.cursor()
        cursor.execute(query, (incoming_message, ))
        results = cursor.fetchall()
        conn.commit()
        output = extract_msisdn(results)

        msisdn = output
        query = "SELECT name, age, county, town, level_of_education, profession, marital_status, religion, ethnicity FROM users WHERE msisdn = %s"
        cursor = conn.cursor()
        cursor.execute(query, (msisdn, ))
        results = cursor.fetchone()
        cursor.close
    
        if results:
            name, age, county, town, level_of_education, profession, marital_status, religion, ethnicity = results
            text = f"{name} aged {age}, {county} county, {town} town,{level_of_education}, {profession}, {marital_status}, {religion}, {ethnicity}"               
            more_text = f"Send DESCRIBE#{msisdn} to get more details"
            response = text + more_text
        return response
        


    else:
        response = "invalid keyword" 
        return response
        

def getuser_id(msisdn):
    query = "SELECT user_id FROM users WHERE msisdn = %s"
    cursor = conn.cursor()
    cursor.execute(query, (msisdn,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None


def check_details(msisdn):
    query = "SELECT * FROM users WHERE msisdn = %s"
    cursor = conn.cursor()
    cursor.execute(query, (msisdn,))
    result = cursor.fetchall()
    cursor.close()
    return result[0] if result else None



def match(age, town, msisdn):
    gender = check_gender(msisdn)
    gender_condition = None

    if gender.lower() == "male":
        gender_condition == 'female'
    elif gender.lower() == "female":
        gender_condition == 'male'

    else:
        return []
    
    query = "SELECT name, msisdn FROM users WHERE age BETWEEN  %s and %s AND town = %s"
    cursor = conn.cursor()
    cursor.execute(query, (age, age, town))
    results = cursor.fetchall()
    row_count = cursor.rowcount
    cursor.close()
    store_matches(results)
    return results, row_count

def displayfirstthree(results):
    if len(results) == 0:
        return "no results found"
    else:
        text =""
        for i, row in enumerate(results[:3]):
            name,msisdn = row
            text += f"  Name: {name}, Msisdn: {msisdn}   . "
        return(f"First three results: "+ text)
    

def store_messages(msisdn, message):
    incoming_message = message
    query = "INSERT INTO messages (msisdn, incoming_message) VALUES (%s,%s)"
    cursor = conn.cursor()
    cursor.execute(query, (msisdn, incoming_message))
    conn.commit
    cursor.close()
    return "Stored as incoming message."



def store_outgoing_messages(msisdn,response):
    outgoing_message = str(response)
    query = "INSERT INTO messages (msisdn,outgoing_message ) VALUES (%s,%s)"
    cursor = conn.cursor()
    cursor.execute(query, (msisdn, outgoing_message))
    conn.commit()
    cursor.close()
    
def normalize_msisdn(msisdn):
    
    if not msisdn.startswith("+254"):
        msisdn = "+254" + msisdn.lstrip("0")
    return msisdn
    


def display_results(results, page):
    start_index = (page - 1) * 3
    end_index = start_index + 3
    sliced_results = results[start_index:end_index]

    if len(sliced_results) == 0:
        return "No more results to display."

    text = "Results:"
    for i, row in enumerate(sliced_results):
        name, msisdn = row
        text += f"{start_index + i + 1}. Name: {name}, Contact: {msisdn}"
    return text

def is_valid_msisdn(msisdn):
    return msisdn.startswith("+254") and len(msisdn) == 12 and msisdn[1:].isdigit()

                   
def check_gender(msisdn):
    query = "SELECT gender FROM users WHERE msisdn = %s"
    cursor = conn.cursor()
    cursor.execute(query, (msisdn,))
    result = cursor.fetchone()
    cursor.close()
    if result and result[0].lower() == "male":
        return "Male"
    elif result and result[0].lower() == "female":
        return "Female"
    else:
        return "Unknown"
    
def fetch_msisdn_details(msisdn):
    query = "SELECT name, age, town FROM users WHERE msisdn = %s"
    cursor = conn.cursor()
    cursor.execute(query, (msisdn, ))
    result = cursor.fetchone()
    cursor.close()
    if result:
                name, age, town = result
                text = f"A man named {name} is interested in you and requested your details. He is aged {age} based in {town}."
                more_text = "Do you want to know him? Send YES to 22141"
   
    print (text + more_text) 



def store_matches(results):
    for name, msisdn in results:
        query = "INSERT INTO matches (name, msisdn ) VALUES (%s,%s)"
        cursor = conn.cursor()
        cursor.execute(query, (name, msisdn))
        conn.commit()
        cursor.close()
    

def select_first_three(results):
    query = "SELECT * FROM matches LIMIT 3"
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return results

def delete_first_three(results):
    query = "DELETE FROM matches LIMIT 3"
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()

def search_msisdn(output):
    msisdn = output
    query = "SELECT name, age, county, level_of_education, profession, marital_status, religion, ethnicity FROM users WHERE msisdn = %s"
    cursor = conn.cursor()
    cursor.execute(query(msisdn, ))
    results = cursor.fetchall()
    cursor.close
    if results:
        name, age, county, town, level_of_education, profession, marital_status, religion, ethnicity = results
        text = f"{name} aged {age}, {county}county, {town}town,{level_of_education}, {profession}, {marital_status}, {religion}, {ethnicity}"               
        more_text = f"Send DESCRIBE#{msisdn} to get more details"
        return jsonify ({"message":text, "more text":more_text})

def extract_msisdn(results):
    msisdn = results[0][0]
    return msisdn

def split_content(content):
    try:
    
        if len(content) ==5:
            name = content[0]
            age = content[1]
            gender = content[2]
            county = content[3]
            town = content[4]

            return{
                "name": name,
                "age": age,
                "gender": gender,
                "county": county,
                "town": town
            }
        else:
            return 
    except Exception as e:
        error_message = "The content does not have enough elements"
        return jsonify(error_message)
def check_name_age_gender(name, age, gender, county, town):
    if not isinstance(name, str) or len(name) <=3:
        response = "invalid name"
        return response
    
    try: 
        age = int(age)
    except ValueError:

        response = "Please enter a valid age number and try again."
        return response
    
    if not (18<= age <= 60):
        response = "you are do not meet rquirements for creating a profile. Age should be between 18 and 60."
        return response
    if not isinstance(gender, str) or gender.lower() not in ['male', 'female']:
        response = "please enter correct gender. Male or female."
        return response
    if not isinstance(county, str) or len(county) <=4:
        response = "provide correct county name"
        return response
    if not isinstance(town, str) or len(town) <=4:
        response = "provide correct town name"
        return response
    return None


def split_details(content):

    try:
    
        if len(content) ==5:
            level_of_education = content[0]
            profession = content[1]
            marital_status = content[2]
            religion = content[3]
            ethnicity = content[4]

            return{
                "level_of_education": level_of_education,
                "profession": profession,
                "marital_status": marital_status,
                "religion": religion,
                "ethnicity": ethnicity
            }
    
        else:
            return 
    except Exception as e:
        error_message = "The content does not have enough elements"

def check_details_content(level_of_education, profession, marital_status, religion, ethnicity):
    if not isinstance(level_of_education, str) or len(level_of_education) <=3:
        response = "check level of education and try again."
        return response
    
    if not isinstance( profession, str) or len(profession) <= 3:
        response = "check profession and try again."
        return response
    if not isinstance(marital_status, str) or marital_status.lower() not in['single', 'married'] or len(marital_status) <=5:
        response = "check marital status and try again. Either single or married."
        return response
    if not isinstance(religion, str) or len(religion) <=4:
        response = "check religion and try again."
        return response
    if not isinstance(ethnicity, str) or len(ethnicity) <=2:
        response = "check ethnicity and try again"
        return response
    return None


def return_at_intervals(resp, reply):
    interval_seconds = 3

    for result in [resp, reply]:
        print(f"returning result: {result}")
        time.sleep(interval_seconds)

def create_tables():
    cursor = conn.cursor()
    # Create the 'users' table
    users_table_query = '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name TEXT(255),
            age INT(3),
            gender TEXT(255),
            county TEXT(255),
            town TEXT(255),
            level_of_education TEXT(255),
            profession TEXT(255),
            marital_status TEXT(255),
            religion TEXT(255),
            ethnicity TEXT(255),
            description TEXT(255)
        )
    '''
    cursor.execute(users_table_query)

    # Create the 'messages' table
    messages_table_query = '''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INT AUTO_INCREMENT PRIMARY KEY,
            incoming_message VARCHAR(300),
            outgoing_message VARCHAR(300),
            msisdn VARCHAR(20),
            `time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    cursor.execute(messages_table_query)

    # Create the 'matches' table
    matches_table_query = '''
        CREATE TABLE IF NOT EXISTS matches (
            name TEXT(255),
            msisdn VARCHAR(20)
        )
    '''
    cursor.execute(matches_table_query)

    conn.commit()
    cursor.close()

       

@app.route('/frontend', methods=['POST'])
def fetch_details():
    req = request.get_json()
    print(req)
    msisdn = req.get("msisdn")
    msisdn = normalize_msisdn(msisdn)
    message =req.get("message")
    create_tables()
    store_messages(msisdn, message)
    respons = handle_message(msisdn, message)
    store_outgoing_messages(msisdn,respons)
    response_data = {"message":respons}
    print(response_data)
    return response_data
    



   

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 5000, debug=True)
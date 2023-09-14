def decode_26(input_string):
    data_dict = {}  # Initialize an empty dictionary to store the data
    key_descriptions = {
            "00": "Reverse Domain Name",
            "01": "Proxy Type",
            "02": "Proxy Value",
            "03": "Editable",
            "04": "Expiry date (Optional)",
            "05": "Transaction Reference (Optional)"
        }
    key_descriptions_proxyType = {'0':'MSIDN','1':'NRIC','2':'UEN'}
        
    while input_string:
        obj_id = input_string[:2]
        obj_len = int(input_string[2:4])
        obj_value = input_string[4:4 + obj_len]
        
        # Define descriptions for each key
        
        # Store the Value and its description in the dictionary with the ID as the key
        if obj_id in key_descriptions:
            data_dict[key_descriptions[obj_id]] = obj_value
        
        # Move to the next data object
        input_string = input_string[4 + obj_len:]
        data_dict

    data_dict['Proxy Type'] = key_descriptions_proxyType[data_dict['Proxy Type']]
    return data_dict
def decode_paynow_qr(qr_code):
    # Split the QR code into individual data objects
    data_objects = []
    while qr_code:
        obj_id = qr_code[:2]
        obj_len = int(qr_code[2:4])
        obj_value = qr_code[4:4 + obj_len]
        data_objects.append((obj_id, obj_value))
        qr_code = qr_code[4 + obj_len:]

    decoded_data = {}
    for obj_id, obj_value in data_objects:
        if obj_id == "00":
            # Payload Format Indicator
            decoded_data["Payload Format Indicator"] = obj_value
        elif obj_id == "01":
            # Point of Initiation Method
            decoded_data["Point of Initiation Method"] = obj_value
        elif obj_id == "26":
            # Merchant Account Information
            merchant_info = decode_26(obj_value)
            decoded_data["Merchant Account Information"] = merchant_info
        elif obj_id == "51":
            # SGQR ID
            decoded_data["SGQR ID"] = obj_value
        elif obj_id == "52":
            # Merchant Category Code
            decoded_data["Merchant Category Code"] = obj_value
        elif obj_id == "53":
            # Transaction Currency
            decoded_data["Transaction Currency"] = obj_value
        elif obj_id == "54":
            # Transaction Amount
            decoded_data["Transaction Amount"] = obj_value
        elif obj_id == "55":
            # Tip or Convenience Indicator
            decoded_data["Tip or Convenience Indicator"] = obj_value
        elif obj_id == "56":
            # Value of Convenience Fee Fixed
            decoded_data["Value of Convenience Fee Fixed"] = obj_value
        elif obj_id == "57":
            # Value of Convenience Fee Percentage
            decoded_data["Value of Convenience Fee Percentage"] = obj_value
        elif obj_id == "58":
            # Country Code
            decoded_data["Country Code"] = obj_value
        elif obj_id == "59":
            # Merchant Name
            decoded_data["Merchant Name"] = obj_value
        elif obj_id == "60":
            # Merchant City
            decoded_data["Merchant City"] = obj_value
        elif obj_id == "61":
            # Postal Code
            decoded_data["Postal Code"] = obj_value
        elif obj_id == "62":
            # Additional Data Field Template
            additional_data = {}
            additional_data["Bill Number"] = obj_value[4:]
            decoded_data["Additional Data Field Template"] = additional_data
        elif obj_id == "63":
            # CRC (Checksum)
            decoded_data["CRC"] = obj_value

    return decoded_data
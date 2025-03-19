from replit.object_storage import Client
import json
import os

def create_or_update_best_params(filename="best_params.json"):
    """Create or update the best_params.json file in Object Storage"""
    # Create an empty dictionary for best parameters
    best_params_data = {}
    
    # First, try to check if the file exists locally
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                best_params_data = json.load(f)
                print(f"Successfully loaded {filename} from local storage")
    except Exception as e:
        print(f"Error reading local file: {e}")
    
    # Now try to use the Object Storage
    try:
        # Initialize Object Storage client
        client = Client()
        
        try:
            # Try to get the file from Object Storage
            json_content = client.download_as_text(filename)
            obj_storage_data = json.loads(json_content)
            print(f"Successfully loaded {filename} from Object Storage")
            
            # If we have data from object storage, use that (it's more up-to-date)
            best_params_data = obj_storage_data
        except Exception as e:
            if "no allowed resources" in str(e):
                print("Object Storage permissions issue. Using local file as fallback.")
            else:
                print(f"File not found in Object Storage or error reading: {e}")
                print(f"Creating new {filename} in Object Storage")
        
        try:
            # Upload to Object Storage
            client.upload_from_text(filename, json.dumps(best_params_data, indent=4))
            print(f"✅ Successfully created/updated '{filename}' in Object Storage")
        except Exception as e:
            print(f"❌ Error uploading to Object Storage: {e}")
            
    except Exception as e:
        print(f"❌ Error initializing Object Storage client: {e}")
    
    # Always save to local file as a backup
    try:
        with open(filename, "w") as f:
            json.dump(best_params_data, f, indent=4)
        print(f"✅ Successfully created/updated local file '{filename}'")
    except Exception as e:
        print(f"Warning: Could not save to local file: {e}")
    
    return best_params_data

if __name__ == "__main__":
    params = create_or_update_best_params()
    print("Initial parameters structure:", params)
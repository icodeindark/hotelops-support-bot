import json, os

SERVICES_FILE = os.path.join("context", "services.json")

def load_services():
    with open(SERVICES_FILE, "r") as f:
        return json.load(f)

def save_services(services):
    with open(SERVICES_FILE, "w") as f:
        json.dump(services, f, indent=2)

def list_services():
    return load_services()

def create_service(service):
    services = load_services()
    services.append(service)
    save_services(services)
    return f"Service {service['name']} created."

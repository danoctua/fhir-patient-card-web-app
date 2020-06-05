import json
import os
import fhirclient.models.observation as o
import fhirclient.models.patient as p
from fhirclient import client

dir_path = os.path.dirname(os.path.realpath(__file__))

config_path = os.path.join(dir_path, "data", "config.json")

with open(config_path) as file:
    settings = json.load(file)


def connect_fo_fhir():
    smart = client.FHIRClient(settings=settings)

    print(f"Connecting to the FHIRServer {settings['api_base']}...")
    print(smart.ready)
    print(smart.prepare())

    patient = p.Patient.read('example', smart.server)
    print(patient.birthDate.isostring)
    # '1963-06-12'
    print(smart.human_name(patient.name[0]))
    print(patient.contact)
    observations = o.Observation.read(patient.id, smart.server)
    print(observations)
    # 'Christy Ebert'


if __name__ == '__main__':
    connect_fo_fhir()

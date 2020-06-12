import requests
from dateutil import parser
import datetime
import numpy as np


class FhirRequest:

    def __init__(self):
        self.r_id = None
        self.last_name = None
        self.first_name = None
        self.current_resource = "patient"
        self.idx_current = 0
        self.idx_count = 50
        self.patient_list = []
        self.observation_list = []
        self.medication_list = []

    def get_patients(self, first_name=None, last_name=None):
        self.idx_current = 0
        self.idx_count = 50
        self.last_name = last_name
        self.first_name = first_name
        self.patient_list = []
        url = f"http://hapi.fhir.org/baseR4/Patient?_format=json&_pretty=true"
        if self.last_name:
            url += f"&family={self.last_name}"
        if self.first_name:
            url += f"&name={self.first_name}"
        r = requests.get(url).json()
        self.r_id = r['id']
        url = f"http://hapi.fhir.org/baseR4?_getpages={self.r_id}&_getpagesoffset={self.idx_current}&_count={self.idx_count}&_format=json&_pretty=true&_bundletype=searchset"
        r = requests.get(url)
        r_json = r.json()
        if 'entry' not in r_json:
            return []
        for patient_dic in r_json['entry']:
            new_patient = Patient()
            if new_patient.upload(patient_dic):
                self.patient_list.append(new_patient)
        self.idx_current += self.idx_count
        return self.patient_list

    def read_patient_data(self, patient_id):
        url = f"http://hapi.fhir.org/baseR4/Patient/{patient_id}?_format=json&_pretty=true"
        r = requests.get(url).json()
        new_patient = Patient()
        if new_patient.upload(r):
            return new_patient
        else:
            return None
        pass

    def read_observation_data(self, observation_id):
        url = f"http://hapi.fhir.org/baseR4/Observation/{observation_id}?_format=json&_pretty=true"
        r = requests.get(url).json()
        new_observation = Observation()
        if new_observation .upload(r):
            return new_observation
        else:
            return None
        pass

    def get_observation_by_patient(self, patient_id, filters=None):
        url = f"http://hapi.fhir.org/baseR4/Observation?patient={patient_id}&_format=json&_pretty=true&_count=200&_sort=-date"
        if isinstance(filters, dict):
            for key in filters:
                for value in filters[key]:
                    url += f"&{key}={value}"
        r = requests.get(url).json()
        self.observation_list = []
        if "entry" not in r:
            return []
        for observation_dic in r["entry"]:
            new_observation = Observation()
            if new_observation.upload(observation_dic):
                self.observation_list.append(new_observation)
        return self.observation_list

    def get_medication_statements_by_patient(self, patient_id):
        url = f"http://hapi.fhir.org/baseR4/MedicationStatement?patient={patient_id}&_format=json&_pretty=true&_count=200"
        r = requests.get(url).json()
        self.medication_list = []
        if "entry" not in r:
            return []
        for medication_dic in r["entry"]:
            new_medication = MedicationStatement()
            if new_medication.upload(medication_dic):
                self.medication_list.append(new_medication)
        return self.medication_list


class Observation:

    def __init__(self, full_url=None, subject_id=None, observation_id=None, status=None, category_display=None,
                 code_display=None, observation_date=None, observation_period=None, last_updated=None, version_id=None,
                 value_quantity_value=None, value_quantity_unit=None, value_concept=None):
        self.resource = "observation"
        self.full_url = full_url
        self.subject_id = subject_id
        self.observation_id = observation_id
        self.status = status
        self.category_display = category_display
        self.code_display = code_display
        self.code = None
        self.observation_date = observation_date
        self.observation_period = observation_period
        self.last_updated = last_updated
        self.version_id = version_id
        self.value_quantity_value = value_quantity_value
        self.value_quantity_unit = value_quantity_unit
        self.value_concept = value_concept
        self.value_sampled_data_flag = False
        self.value_sampled_data_period = None
        self.value_sampled_data_factor = None
        self.value_sampled_data_lower_limit = None
        self.value_sampled_data_upper_limit = None
        self.value_sampled_data_data = None

    def upload(self, observation_dic):

        def check_int(str_dig):
            try:
                int(str_dig)
                return True
            except:
                return False
        try:
            self.full_url = observation_dic["fullUrl"] if "fullUrl" in observation_dic else None
            if "resource" in observation_dic:
                observation_dic = observation_dic["resource"]
            self.subject_id = observation_dic["subject"]["reference"]
            self.observation_id = observation_dic['id']
            self.status = observation_dic["status"]
            self.category_display = [observation_dic["category"][x]['coding'][0]['display']
                                for x in range(len(observation_dic["category"]))] \
                if 'category' in observation_dic else []
            if "code" in observation_dic:
                if "text" in observation_dic["code"]:
                    self.code_display = [observation_dic["code"]["text"]]
                    tmp_ = []
                    for x in range(len(observation_dic["code"]["coding"])):
                        if "code" in observation_dic["code"]["coding"][x]:
                            tmp_.append(observation_dic["code"]["coding"][x]["code"])
                    self.code = tmp_
                else:
                    tmp = []
                    tmp_ = []
                    for x in range(len(observation_dic["code"]["coding"])):
                        found = False
                        if "display" in observation_dic["code"]["coding"][x]:

                            tmp.append(observation_dic["code"]["coding"][x]["display"])
                            found = True
                        if "code" in observation_dic["code"]["coding"][x]:
                            if not found:
                                tmp.append(observation_dic["code"]["coding"][x]["code"])
                            tmp_.append(observation_dic["code"]["coding"][x]["code"])
                    self.code = tmp_
                    self.code_display = tmp
            self.observation_date = parser.parse(observation_dic['effectiveDateTime']).replace(tzinfo=None) \
                if 'effectiveDateTime' in observation_dic else None
            self.observation_period = observation_dic['effectivePeriod'] \
                if 'effectivePeriod' in observation_dic else None
            self.last_updated = parser.parse(observation_dic["meta"]['lastUpdated']).replace(tzinfo=None)
            self.version_id = observation_dic["meta"]['versionId']
            if "valueSampledData" in observation_dic:
                self.value_sampled_data_flag = True
                self.value_sampled_data_period = observation_dic["valueSampledData"]["period"]
                self.value_sampled_data_factor = observation_dic["valueSampledData"]["factor"]
                self.value_sampled_data_lower_limit = observation_dic["valueSampledData"]["lowerLimit"]
                self.value_sampled_data_upper_limit = observation_dic["valueSampledData"]["upperLimit"]
                self.value_sampled_data_data = list(map(int,
                                                        filter(lambda x: check_int(x),
                                                               observation_dic["valueSampledData"]["data"].split(","))))
            if "valueQuantity" in observation_dic:
                self.value_quantity_value = observation_dic["valueQuantity"]["value"]
                self.value_quantity_unit = observation_dic["valueQuantity"]["unit"]
            if "valueCodeableConcept" in observation_dic:
                if "text" in observation_dic["valueCodeableConcept"]:
                    self.value_concept = observation_dic["valueCodeableConcept"]["text"]
                elif "display" in observation_dic["valueCodeableConcept"]:
                    self.value_concept = observation_dic["valueCodeableConcept"]["display"]
            return True
        except Exception as exp:
            print(exp, observation_dic)
            return False

    def get_subject_id(self):
        return "/".join(self.subject_id.split("/")[1:]) if self.subject_id else ""

    def get_category_display(self):
        return ", ".join(self.category_display) if self.category_display else "Observation"

    def get_code_display(self):
        return (", ".join(self.code_display) if self.code_display else None) or self.value_concept or\
               ("Sampled data" if self.value_sampled_data_flag else None) or "No description"

    def get_code(self):
        return ",".join(self.code)

    def get_observation_date_display(self):
        return self.observation_date.date() if self.observation_date else "--.--.--"

    def get_observation_time_display(self):
        return self.observation_date.time() if self.observation_date else "--:--:--"

    def get_quantity_value_display(self):
        if self.value_quantity_value:
            return self.value_quantity_value
        elif self.value_concept:
            return self.value_concept
        else:
            return "No value"

    def get_quantity_value_float(self, precision=2):
        try:
            return round(self.get_quantity_value_display(), precision)
        except:
            return 0

    def get_quantity_unit_display(self):
        if self.value_quantity_unit:
            return self.value_quantity_unit
        else:
            return ""

    def get_event_date(self):
        return self.observation_date if self.observation_date else None

    def get_value_sampled_data(self):
        return np.array(self.value_sampled_data_data)

    def check_quantity_value_isnumeric(self):
        try:
            int(self.get_quantity_value_display())
            return True
        except:
            return False

    def check_date_is_between(self, lower_bound, upper_bound):
        if self.get_event_date() and isinstance(self.get_event_date(), datetime.datetime):
            if lower_bound <= self.get_event_date() <= upper_bound:
                return True
        return False


class Patient:

    def __init__(self, full_url=None, patient_id=None, last_name=None, first_names=None, gender=None,
                 telecom_system=None, telecom_value=None, birth_date=None,
                 address_text=None, address_city=None, address_state=None, address_postal_code=None):
        """
        :param full_url: full url in fhir database
        :param patient_id:
        :param last_name:
        :param first_names: list of first names
        :param gender: gender: male, female, None
        :param telecom_system: system which patient use to contact
        :param telecom_value: mobile phone or email
        :param birth_date: full birth date in datetime format
        :param address_text: street and home number
        :param address_city:
        :param address_state:
        :param address_postal_code:
        """
        self.resource = "patient"
        self.full_url = full_url
        self.patient_id = patient_id
        self.last_name = last_name
        self.first_names = first_names
        self.gender = gender
        self.telecom_system = telecom_system
        self.telecom_value = telecom_value
        self.birth_date = birth_date
        self.address_text = address_text
        self.address_city = address_city
        self.address_state = address_state
        self.address_postal_code = address_postal_code

    def get_first_names_display(self):
        return " ".join(self.first_names) if self.first_names else ""

    def get_patient_id_display(self):
        return self.patient_id[:8]

    def get_gender_display(self):
        if self.gender:
            if 'female' in self.gender:
                return "♀ " + self.gender
            elif 'male' in self.gender:
                return "♂ " + self.gender
            else:
                return self.gender
        else:
            return "unknown"

    def get_address_display(self):
        return ", ".join(filter(None, [self.address_text, self.address_city,
                                       self.address_state, self.address_postal_code]))

    def get_contact_display(self):
        return ": ".join(filter(None, [self.telecom_system, self.telecom_value]))

    def get_birth_date_display(self):
        return self.birth_date.date() if self.birth_date else "No birth date"

    def __str__(self):
        res = "{:_>30}\n".format("")
        res += f"PATIENT {self.patient_id}\n"
        res += "{:_>30}\n".format("")
        res += f"Last Name: {self.last_name}\n"
        res += f"First Names: {self.first_names}\n"
        res += f"Gender: {self.gender}\n"
        res += f"Birth date: {self.birth_date}\n\n"
        return res

    def upload(self, patient_dic):
        try:
            self.full_url = patient_dic["fullUrl"] if "fullUrl" in patient_dic else None
            if 'resource' in patient_dic:
                patient_dic = patient_dic['resource']
            self.patient_id = patient_dic['id']
            if "name" in patient_dic:
                self.last_name = patient_dic['name'][0]['family'] \
                    if 'family' in patient_dic['name'][0] else None
                self.first_names = patient_dic['name'][0]['given'] \
                    if 'given' in patient_dic['name'][0] else None
            self.gender = patient_dic['gender'] if 'gender' in patient_dic else None
            if "telecom" in patient_dic:
                self.telecom_system = patient_dic['telecom'][0]['system'] if "system" in \
                                                                                    patient_dic['telecom'][
                                                                                        0] else None
                self.telecom_value = patient_dic['telecom'][0]['value'] if "value" in \
                                                                                  patient_dic['telecom'][
                                                                                      0] else None
            self.birth_date = parser.parse(patient_dic['birthDate']) if "birthDate" in patient_dic else None
            if "address" in patient_dic:
                self.address_text = patient_dic['address'][0]['text'] if "text" in \
                                                                                patient_dic['address'][
                                                                                    0] else None
                self.address_city = patient_dic['address'][0]['city'] if "city" in \
                                                                                patient_dic['address'][
                                                                                    0] else None
                self.address_state = patient_dic['address'][0]['state'] if "state" in \
                                                                                  patient_dic['address'][
                                                                                      0] else None
                self.address_postal_code = patient_dic['address'][0]['postalCode'] if "postalCode" in \
                                                                                             patient_dic[
                                                                                                 'address'][0] else None
            return True
        except:
            return False


class MedicationStatement:

    def __init__(self):
        self.resource = "medication_statements"
        self.full_url = None
        self.statement_id = None
        self.patient_id = None
        self.version = None
        self.last_updated = None
        self.coding_code = None
        self.coding_display = None
        self.dosage_text = None
        self.dosage_timing_repeat = True
        self.dosage_timing_frequency = None
        self.dosage_timing_period = None
        self.dosage_timing_period_unit = None
        self.value_sampled_data_flag = None

    def upload(self, medicament_dic):
        try:
            self.full_url = medicament_dic["fullUrl"]
            medicament_dic = medicament_dic["resource"]
            self.statement_id = medicament_dic["id"]
            self.version = medicament_dic["meta"]["versionId"]
            self.last_updated = parser.parse(medicament_dic["meta"]["lastUpdated"]).replace(tzinfo=None)
            if "medicationCodeableConcept" in medicament_dic:
                if "text" in medicament_dic["medicationCodeableConcept"]:
                    self.coding_display = medicament_dic["medicationCodeableConcept"]["text"]
                elif "coding" in medicament_dic["medicationCodeableConcept"]:
                    self.coding_code = medicament_dic["medicationCodeableConcept"]["coding"][0]["code"]
                    if "display" in medicament_dic["medicationCodeableConcept"]["coding"][0]["code"]:
                        self.coding_display = medicament_dic["medicationCodeableConcept"]["coding"][0]["code"]["display"]
            if "dosage" in medicament_dic:

                if "text" in medicament_dic["dosage"][0]:
                    self.dosage_text = medicament_dic["dosage"][0]["text"]
                if "timing" in medicament_dic["dosage"][0]:

                    if "repeat" in medicament_dic["dosage"][0]["timing"]:
                        self.dosage_timing_repeat = True
                        if "frequency" in medicament_dic["dosage"][0]["timing"]["repeat"]:
                            self.dosage_timing_frequency = medicament_dic["dosage"][0]["timing"]["repeat"]["frequency"]
                        if "period" in medicament_dic["dosage"][0]["timing"]["repeat"]:
                            self.dosage_timing_period = medicament_dic["dosage"][0]["timing"]["repeat"]["period"]
                        if "periodUnit" in medicament_dic["dosage"][0]["timing"]["repeat"]:
                            self.dosage_timing_period_unit = medicament_dic["dosage"][0]["timing"]["repeat"]["periodUnit"]
            return True
        except Exception as exp:
            print(exp, medicament_dic)
            return False

    def get_event_date(self):
        return self.last_updated if self.last_updated else None

    def get_event_date_display(self):
        return self.last_updated.date() if self.last_updated else "--.--.--"

    def get_event_time_display(self):
        return self.last_updated.strftime("%H:%M:%S") if self.last_updated else "--:--:--"

    def get_code_display(self):
        if self.coding_display:
            return self.coding_display + ": " + self.dosage_text if self.dosage_text else ""
        elif self.coding_code:
            return self.coding_code
        else:
            return "No description"

    def get_category_display(self):
        return "Medication Statement"

    def get_quantity_value_display(self):
        if self.dosage_timing_repeat:
            return str(self.dosage_timing_frequency) + "&times;" + str(self.dosage_timing_period)
        else:
            return 0

    def get_quantity_unit_display(self):
        if self.dosage_timing_repeat:
            return self.dosage_timing_period_unit
        else:
            return ""

    def check_date_is_between(self, lower_bound, upper_bound):
        if self.get_event_date() and isinstance(self.get_event_date(), datetime.datetime):
            if lower_bound <= self.get_event_date() <= upper_bound:
                return True
        return False


def main():
    fhir_req = FhirRequest()
    fhir_req.get_patients()
    for patient in fhir_req.patient_list[:30]:
        observations = fhir_req.get_observation_by_patient(patient.patient_id)
        # print(observations)
        # print(patient)


if __name__ == '__main__':
    main()
    # fhir_req = FhirRequest()

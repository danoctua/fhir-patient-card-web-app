import requests
from dateutil import parser
import datetime
import numpy as np


class FhirRequest:

    def __init__(self):
        self.r_id = None
        self.last_name = None
        self.first_name = None
        self.current_resource = None
        self.idx_current = 0
        self.idx_count = 50
        self.current_page = 1
        self.next_exists = False
        self.patient_list = []
        self.observation_list = []
        self.medication_list = []
        self.total_count = None
        self.total = None

    def get_r_id(self, first_name=None, last_name=None):
        self.last_name = last_name
        self.first_name = first_name
        url = f"http://hapi.fhir.org/baseR4/Patient?_format=json&_pretty=true"
        if self.last_name:
            url += f"&family={self.last_name}"
        if self.first_name:
            url += f"&name={self.first_name}"
        r = requests.get(url).json()
        self.r_id = r['id']
        self.idx_current = 0
        self.idx_count = 50
        self.current_resource = "patient"

    def get_patients(self, first_name=None, last_name=None, page_num=None):
        self.total = None
        if first_name != self.first_name or last_name != self.last_name or self.current_resource != "patient":
            self.get_r_id(first_name=first_name, last_name=last_name)
        elif page_num and isinstance(page_num, int):
            if page_num > self.current_page:
                self.current_page += 1
                self.idx_current += self.idx_count
            else:
                self.current_page = page_num
                self.idx_current = self.idx_count * (page_num - 1)

        self.patient_list = []
        url = f"http://hapi.fhir.org/baseR4?_getpages={self.r_id}&_getpagesoffset={self.idx_current}&_count={self.idx_count}&_format=json&_pretty=true&_bundletype=searchset"
        r = requests.get(url)
        r_json = r.json()
        if 'entry' not in r_json:
            return []
        if "link" in r_json:
            self.next_exists = False
            for entry in r_json["link"]:
                if entry["relation"] == "next":
                    self.next_exists = True
                    break
        for patient_dic in r_json['entry']:
            new_patient = Patient()
            if new_patient.upload(patient_dic):
                self.patient_list.append(new_patient)
        self.idx_current += self.idx_count
        return self.patient_list

    def read_patient_data(self, patient_id, json=False, version=None):
        if not self.total or self.current_resource != "patient":
            self.current_resource = "patient"
            url = f"http://hapi.fhir.org/baseR4/Patient/{patient_id}/_history?_format=json"
            req = requests.get(url)
            setted = False
            if req.status_code == 200:
                r = req.json()
                if "total" in r:
                    self.total = r["total"]
                    setted = True
            if not setted:
                self.total = 1

        if not version:
            url = f"http://hapi.fhir.org/baseR4/Patient/{patient_id}?_format=json&_pretty=true"
        else:
            url = f"http://hapi.fhir.org/baseR4/Patient/{patient_id}/_history/{version}?_format=json&_pretty=true"
        req = requests.get(url)
        if req.status_code != 200:
            return None
        r = req.json()
        if "total" in r:
            self.total = r["total"]
        if json:
            return r
        new_patient = Patient()
        if new_patient.upload(r, self):
            return new_patient
        else:
            return None
        pass

    def read_observation_data(self, observation_id, json=False, version=None):
        if not self.total or self.current_resource != "observation":
            self.current_resource = "observation"
            url = f"http://hapi.fhir.org/baseR4/Observation/{observation_id}/_history?_format=json"
            req = requests.get(url)
            setted = False
            if req.status_code == 200:
                r = req.json()
                if "total" in r:
                    self.total = r["total"]
                    setted = True
            if not setted:
                self.total = 1
        if not version:
            url = f"http://hapi.fhir.org/baseR4/Observation/{observation_id}?_format=json&_pretty=true"
        else:
            url = f"http://hapi.fhir.org/baseR4/Observation/{observation_id}/_history/{version}?_format=json&_pretty=true"
        req = requests.get(url)
        if req.status_code != 200:
            return None
        r = req.json()
        if "total" in r:
            self.total = r["total"]
        if json:
            return r
        new_observation = Observation()
        if new_observation.upload(r):
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

    def update_patient_data(self, patient_id, updates):
        url = f"http://hapi.fhir.org/baseR4/Patient/{patient_id}?_format=json&_pretty=true"
        patient_data = self.read_patient_data(patient_id, json=True)
        if not patient_data or not isinstance(patient_data, dict):
            # print("No patient")
            return ["danger", f"No patient with id {patient_id}"]
        headers = {"content-type": "application/fhir+json; charset=UTF-8"}
        created = False
        for sub in ["text", "city", "state"]:
            if "address_" + sub in updates:
                if 'address' not in patient_data:
                    patient_data["address"] = [{}]
                    created = True
                patient_data["address"][0][sub] = updates["address_" + sub]
                if created and sub != "text":
                    patient_data["address"][0]["text"] = updates["address_" + sub]
                break

        r = requests.put(url, json=patient_data, headers=headers)

        if r.status_code == 200:
            return ["success", "All data has been updated"]
        else:
            return ["danger", f"Response code: {r.status_code}. Message: {r.text}"]

    def update_observation_data(self, observation_id, updates):
        url = f"http://hapi.fhir.org/baseR4/Observation/{observation_id}?_format=json&_pretty=true"
        observation_data = self.read_observation_data(observation_id, json=True)
        if not observation_data or not isinstance(observation_data, dict):
            return ["danger", f"No obsevation with id {observation_id}"]
        headers = {"content-type": "application/fhir+json; charset=UTF-8"}
        for sub in ["date", "time"]:
            if "observation_" + sub in updates:
                if 'effectiveDateTime' not in observation_data:
                    observation_data["effectiveDateTime"] = datetime.datetime(1900, 1, 1, 1, 1)
                date_converted = parser.parse(observation_data["effectiveDateTime"])
                if sub == "date":
                    year, month, day = updates["observation_" + sub].split("-")
                    observation_data["effectiveDateTime"] = date_converted.replace(year=int(year),
                                                                                   month=int(month),
                                                                                   day=int(day)).strftime("%Y-%m-%dT%H:%M:%S")

                elif sub == "time":
                    hour, minute, seconds = updates["observation_" + sub].split(":")
                    observation_data["effectiveDateTime"] = date_converted.replace(hour=int(hour),
                                                                                   minute=int(minute),
                                                                                   second=int(seconds)).strftime("%Y-%m-%dT%H:%M:%S")
                break

        r = requests.put(url, json=observation_data, headers=headers)

        if r.status_code == 200:
            return ["success", "All data has been updated"]
        else:
            return ["danger", f"Response code: {r.status_code}. Message: {r.text}"]


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
            self.subject_id = observation_dic["subject"]["reference"] if "subject" in observation_dic else "Patient/unknwon"
            self.observation_id = observation_dic['id']
            self.status = observation_dic["status"] if "status" in observation_dic else "unknown"
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
            self.version_id = int(observation_dic["meta"]['versionId'])
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
        return (", ".join(self.code_display) if self.code_display else None) or self.value_concept or \
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

    def get_last_updated(self):
        return self.last_updated.strftime("%Y-%m-%d %H:%M:%S")


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
        self.version_id = None
        self.last_updated = None
        self.identifiers = []

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
        return ", ".join(filter(None, [self.address_text]))

    def get_contact_display(self):
        return ": ".join(filter(None, [self.telecom_system, self.telecom_value]))

    def get_birth_date_display(self):
        return self.birth_date.date() if self.birth_date else "No birth date"

    def get_identifiers_display(self):
        if self.identifiers:
            tmp = ""
            for id_ in self.identifiers:
                for key in id_:
                    tmp += str(key) + ": " + str(id_[key]) + "<br>"
            return tmp
        else:
            return "No identifiers"

    def get_version_id(self):
        return self.version_id + 1

    def get_address_state(self):
        return self.address_state if self.address_state else ""

    def get_address_city(self):
        return self.address_city if self.address_city else ""

    def get_last_updated(self):
        return self.last_updated.strftime("%Y-%m-%d at %H:%M:%S") if self.last_updated else "No date"

    def __str__(self):
        res = "{:_>30}\n".format("")
        res += f"PATIENT {self.patient_id}\n"
        res += "{:_>30}\n".format("")
        res += f"Last Name: {self.last_name}\n"
        res += f"First Names: {self.first_names}\n"
        res += f"Gender: {self.gender}\n"
        res += f"Birth date: {self.birth_date}\n\n"
        return res

    def upload(self, patient_dic, fhir=None):
        try:
            self.full_url = patient_dic["fullUrl"] if "fullUrl" in patient_dic else None
            if 'resource' in patient_dic:
                patient_dic = patient_dic['resource']
            if "meta" in patient_dic:
                self.version_id = int(patient_dic["meta"]["versionId"]) if 'versionId' in patient_dic["meta"] else 0
                if fhir:
                    if self.version_id > fhir.total:
                        fhir.total = self.version_id
                self.last_updated = parser.parse(patient_dic["meta"]["lastUpdated"]) if 'lastUpdated' in patient_dic[
                    "meta"] else None
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
            if "identifier" in patient_dic:
                for id_ in patient_dic["identifier"]:
                    if "type" in id_ and 'value' in id_:
                        if "value" in id_:
                            self.identifiers.append({id_["type"]["text"]: id_["value"]})
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
                        self.coding_display = medicament_dic["medicationCodeableConcept"]["coding"][0]["code"][
                            "display"]
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
                            self.dosage_timing_period_unit = medicament_dic["dosage"][0]["timing"]["repeat"][
                                "periodUnit"]
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

import requests


class FhirRequest:

    def __init__(self, last_name=None, first_name=None, idx_start=0, idx_count=50):
        self.r_id = None
        self.last_name = last_name
        self.first_name = first_name
        self.idx_current = idx_start
        self.idx_count = idx_count
        self.patient_list = []
        url = f"http://hapi.fhir.org/baseR4/Patient?_format=json&_pretty=true"
        if last_name:
            url += f"&family={last_name}"
        if first_name:
            url += f"&name={first_name}"
        r = requests.get(url)
        r_json = r.json()
        self.r_id = r_json['id']

    def get_patients(self):
        self.patient_list = []
        url = f"http://hapi.fhir.org/baseR4?_getpages={self.r_id}&_getpagesoffset={self.idx_current}&_count={self.idx_count}&_format=json&_pretty=true&_bundletype=searchset"
        r = requests.get(url)
        r_json = r.json()
        for patient_dic in r_json['entry']:
            try:
                full_url = patient_dic["fullUrl"]
                patient_id = patient_dic['resource']['id']
                if "name" in patient_dic['resource']:
                    last_name = patient_dic['resource']['name'][0]['family']\
                        if 'family' in patient_dic['resource']['name'][0] else None
                    first_names = patient_dic['resource']['name'][0]['given'] \
                        if 'given' in patient_dic['resource']['name'][0] else None
                else:
                    last_name, first_names = None, []
                gender = patient_dic['resource']['gender'] if 'gender' in patient_dic['resource'] else None
                if "telecom" in patient_dic['resource']:
                    telecom_system = patient_dic['resource']['telecom'][0]['system'] if "system" in \
                                                                                        patient_dic['resource']['telecom'][
                                                                                            0] else None
                    telecom_value = patient_dic['resource']['telecom'][0]['value'] if "value" in \
                                                                                      patient_dic['resource']['telecom'][
                                                                                          0] else None
                else:
                    telecom_system, telecom_value = None, None
                birth_date = patient_dic['resource']['birthDate'] if "birthDate" in patient_dic['resource'] else None
                if "address" in patient_dic["resource"]:
                    address_text = patient_dic['resource']['address'][0]['text'] if "text" in \
                                                                                    patient_dic['resource']['address'][
                                                                                        0] else None
                    address_city = patient_dic['resource']['address'][0]['city'] if "city" in \
                                                                                    patient_dic['resource']['address'][
                                                                                        0] else None
                    address_state = patient_dic['resource']['address'][0]['state'] if "state" in \
                                                                                      patient_dic['resource']['address'][
                                                                                          0] else None
                    address_postal_code = patient_dic['resource']['address'][0]['postalCode'] if "postalCode" in \
                                                                                                 patient_dic['resource'][
                                                                                                     'address'][0] else None
                else:
                    address_text, address_city, address_state, address_postal_code = [None] * 4
                new_patient = Patient(full_url, patient_id, last_name, first_names, gender, telecom_system, telecom_value,
                                      birth_date,
                                      address_text, address_city, address_state, address_postal_code)
                self.patient_list.append(new_patient)
            except Exception as exp:
                print(exp, patient_dic)
                return
        self.idx_current += self.idx_count


class Patient:

    def __init__(self, full_url, patient_id, last_name, first_names, gender, telecom_system, telecom_value, birth_date,
                 address_text, address_city, address_state, address_postal_code):
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

    def __str__(self):
        res = ""
        res += "{:_>30}\n".format("")
        res += f"PATIENT {self.patient_id}\n"
        res += "{:_>30}\n".format("")
        res += f"Last Name: {self.last_name}\n"
        res += f"First Names: {self.first_names}\n"
        res += f"Gender: {self.gender}\n"
        res += f"Birth date: {self.birth_date}\n\n"
        return res


def main():
    fhir_req = FhirRequest(last_name="Smith")
    fhir_req.get_patients()
    for patient in fhir_req.patient_list:
        print(patient)


if __name__ == '__main__':
    main()
    # fhir_req = FhirRequest()

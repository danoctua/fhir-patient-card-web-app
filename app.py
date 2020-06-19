from flask import Flask, render_template, url_for, request, redirect, session
from tools import *

app = Flask(__name__)

app.secret_key = 'FHIR will destroy you'
app.config['SESSION_TYPE'] = 'filesystem'

fhir_req = FhirRequest()


@app.route("/")
def main_page():
    return redirect(url_for("patients_page"))


@app.route("/patients")
@app.route("/patients/<int:page_num>")
def patients_page(page_num=1):
    if page_num > fhir_req.current_page + 1:
        return redirect(url_for("patients_page", page_num=fhir_req.current_page+1))
    session["BACK_URL_PATIENT"] = request.url
    given, family = None, None

    def get_redirect_url(new_req_val):
        url_tmp = "?"
        for item in new_req_val:
            url_tmp += item + "=" + new_req_val[item]
        new_url = request.path + url_tmp
        return new_url

    req_val = request.values.to_dict()
    if "given_" in req_val:
        del req_val["given_"]
        if "given" in req_val:
            del req_val["given"]
        return redirect(get_redirect_url(req_val))
    elif "family_" in req_val:
        del req_val["family_"]
        if "family" in req_val:
            del req_val["family"]
        return redirect(get_redirect_url(req_val))
    if "given" in req_val and req_val['given'] != "":
        given = req_val["given"]
    if "family" in req_val and req_val['family'] != "":
        family = req_val["family"]
    patients = fhir_req.get_patients(first_name=given, last_name=family, page_num=page_num)
    return render_template("patients.html", patients=patients, given=given, family=family,
                           current_url=request.url, page_num=page_num)


@app.route("/patient/<patient_id>", methods=["POST"])
def patient_page_post(patient_id: str):
    req_val = request.values.to_dict()
    res = fhir_req.update_patient_data(patient_id, req_val)
    session["notification"] = res
    return redirect(url_for("patient_page", patient_id=patient_id))


@app.route("/patient/<patient_id>")
def patient_page(patient_id: str):
    back_url = session["BACK_URL_PATIENT"] if "BACK_URL_PATIENT" in session else None
    if not back_url:
        back_url = url_for("patients_page")
    notification = session["notification"] if "notification" in session else None
    session["notification"] = None
    session["BACK_URL_OBSERVATION"] = request.url
    r_val = request.values.to_dict()
    version = int(r_val["version"]) if 'version' in r_val else None
    patient = fhir_req.read_patient_data(patient_id, version=version)
    if not patient:
        session["notification"] = ["danger", "No such a patient in database"]
        return redirect(url_for("patients_page"))
    if patient.version_id > 1:
        prev_patient = fhir_req.read_patient_data(patient_id, version=max(patient.version_id - 1, 1))
    else:
        prev_patient = patient
    if not prev_patient:
        prev_patient = patient
    max_version = fhir_req.total + 1 if fhir_req.total else patient.version_id + 1
    lower_date = datetime.datetime(1900, 1, 1, 1, 1).strftime("%Y-%m-%d")
    lower_date_datetime = datetime.datetime.strptime(lower_date, "%Y-%m-%d")
    upper_date = datetime.datetime.now().strftime("%Y-%m-%d")
    upper_date_datetime = datetime.datetime.strptime(upper_date, "%Y-%m-%d")
    if "from" in r_val:
        lower_date = r_val["from"]
        lower_date_datetime = datetime.datetime.strptime(lower_date, "%Y-%m-%d")
    if "to" in r_val:
        upper_date = r_val["to"]
        upper_date_datetime = datetime.datetime.strptime(upper_date, "%Y-%m-%d")
    observations = fhir_req.get_observation_by_patient(patient_id)
    observations = list(filter(lambda x: x.check_date_is_between(lower_date_datetime, upper_date_datetime), observations))
    m_statements = fhir_req.get_medication_statements_by_patient(patient_id)
    # m_statements = list(filter(lambda x: x.check_date_is_between(lower_date_datetime, upper_date_datetime), m_statements))
    events = observations + m_statements
    events = list(sorted(events, key=lambda x: x.get_event_date() or datetime.datetime.min, reverse=True))
    return render_template("patient.html", patient=patient, observations=observations,
                           m_statements=m_statements, events=events, back_url=back_url,
                           upper_date=upper_date, lower_date=lower_date, current_url=request.path,
                           notification=notification, version=version, max_version=max_version,
                           prev_patient=prev_patient)


@app.route("/observation/<observation_id>", methods=["POST"])
def observation_page_post(observation_id: str):
    req_val = request.values.to_dict()
    res = fhir_req.update_observation_data(observation_id, req_val)
    session["notification"] = res
    return redirect(url_for("observation_page", observation_id=observation_id))


@app.route("/observation/<observation_id>")
def observation_page(observation_id: str):
    back_url = session["BACK_URL_OBSERVATION"] if "BACK_URL_OBSERVATION" in session else None
    notification = session["notification"] if "notification" in session else None
    session["notification"] = None
    r_val = request.values.to_dict()
    version = int(r_val["version"]) if 'version' in r_val else None
    observation = fhir_req.read_observation_data(observation_id, version=version)
    if not observation:
        return redirect(back_url)
    if observation.version_id > 1:
        prev_observation = fhir_req.read_observation_data(observation_id, version=max(observation.version_id - 1, 1))
    else:
        prev_observation = observation
    max_version = fhir_req.total + 1 if fhir_req.total else observation.version_id + 1
    observation_compare = {}
    lower_date = datetime.datetime(1900, 1, 1, 1, 1).strftime("%Y-%m-%d")
    lower_date_datetime = datetime.datetime.strptime(lower_date, "%Y-%m-%d")
    upper_date = datetime.datetime.now().strftime("%Y-%m-%d")
    upper_date_datetime = datetime.datetime.strptime(upper_date, "%Y-%m-%d")
    if observation.check_quantity_value_isnumeric():
        r_val = request.values.to_dict()
        if "from" in r_val:
            lower_date = r_val["from"]
            lower_date_datetime = datetime.datetime.strptime(lower_date, "%Y-%m-%d")
        if "to" in r_val:
            upper_date = r_val["to"]
            upper_date_datetime = datetime.datetime.strptime(upper_date, "%Y-%m-%d")
        tmp = fhir_req.get_observation_by_patient(observation.get_subject_id(),
                                                  {"code": [observation.get_code()]})
        tmp = list(filter(lambda x: x.check_date_is_between(lower_date_datetime, upper_date_datetime), tmp))
        observation_compare = filter_objects_valid(list(reversed(tmp)))
    return render_template("observation.html", observation=observation, back_url=back_url,
                           get_labels=get_labels, observation_compare=observation_compare,
                           lower_date=lower_date, upper_date=upper_date, notification=notification,
                           max_version=max_version, prev_observation=prev_observation)


def filter_objects_valid(ls_objects):
    objects = []
    for obj in ls_objects:
        if obj.check_quantity_value_isnumeric() and obj.get_event_date():
            objects.append(obj)
    return objects


def get_labels(array):
    # return np.linspace(start=0, stop=len(array), num=)
    return range(len(array))


if __name__ == '__main__':
    app.run(debug=True)

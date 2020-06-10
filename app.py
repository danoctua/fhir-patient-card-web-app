from flask import Flask, render_template, url_for, request, redirect, session
from fhir_test import *
import numpy as np

app = Flask(__name__)

app.secret_key = 'FHIR will destroy you'
app.config['SESSION_TYPE'] = 'filesystem'


@app.route("/")
def main_page():
    return redirect(url_for("patients_page"))


@app.route("/patients")
def patients_page():
    session["BACK_URL"] = request.url
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
    fhir_req = FhirRequest()
    patients = fhir_req.get_patients(first_name=given, last_name=family)
    return render_template("patients.html", patients=patients, given=given, family=family,
                           current_url=request.url)


@app.route("/patient/<patient_id>")
def patient_page(patient_id: str):
    back_url = session["BACK_URL"] if "BACK_URL" in session else None
    if not back_url:
        back_url = url_for("patients_page")
    session["BACK_URL"] = request.url
    fhir_req = FhirRequest()
    patient = fhir_req.read_patient_data(patient_id)
    if not patient:
        return redirect(url_for("patients_page"))
    observations = fhir_req.get_observation_by_patient(patient_id)
    m_statements = fhir_req.get_medication_statements_by_patient(patient_id)
    events = observations + m_statements
    events = list(sorted(events, key=lambda x: x.get_event_date() or datetime.datetime.min, reverse=True))
    return render_template("patient.html", patient=patient, observations=observations,
                           m_statements=m_statements, events=events, back_url=back_url)


@app.route("/observation/<observation_id>")
def observation_page(observation_id: str):
    fhir_req = FhirRequest()
    observation = fhir_req.read_observation_data(observation_id)
    return render_template("observation.html", observation=observation)


def get_labels(array):
    return np.linspace(start=0, stop=len(array), num=10)


if __name__ == '__main__':
    app.run(debug=True)

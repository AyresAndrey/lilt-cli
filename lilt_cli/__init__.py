import os
import json
import time
import requests
import xml.etree.ElementTree as ET

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

lilt_api_url = "https://lilt.com/2"

def pretranslate_document(document_id):
    payload = {"key": os.environ["LILT_API_KEY"]}
    jsonData = { "id": document_id}
    headers = { "Content-Type": "application/json" }
    res = requests.post(lilt_api_url + "/documents/pretranslate", params=payload, data=json.dumps(jsonData), headers=headers, verify=False)
    return res.json()

def get_seguiments(docid):
    payload = {"key": os.environ["LILT_API_KEY"], "id": docid, "is_xliff": "true"}
    res = requests.get(lilt_api_url + "/documents/files", params=payload, verify=False)
    root = ET.fromstring(res.content)
    namespace = '{urn:oasis:names:tc:xliff:document:1.2}'
    seguiments = {}
    for child in root.findall(".//%strans-unit" % namespace):
        id = child.attrib['resname']
        try:
            target = child.find(".//%s%s" % (namespace, "target"))
            source = child.find(".//%s%s" % (namespace, "source"))
            seguiments[id] = {
                "translation":  target.text,
                "source":  source.text,
                "id":  id
            }
        except:
            pass
    return seguiments

def get_all_documents(project_id, name=None):
    payload = {"key": os.environ["LILT_API_KEY"], "id": project_id}
    res = requests.get(lilt_api_url + "/projects", params=payload, verify=False)
    allproj = res.json()
    documents = []
    for proj in allproj:
        for doc in proj["document"]:
            if name == doc['name']:
                documents.append(doc)
    return documents

def get_all_seguiments_by_project(project_id):
    payload = {"key": os.environ["LILT_API_KEY"], "id": project_id}
    res = requests.get(lilt_api_url + "/projects", params=payload, verify=False)
    allproj = res.json()
    all_seguiments = {}
    for proj in allproj:
        if not 'document' in proj:
            continue

        for doc in proj["document"]:
            seguiments = get_seguiments(doc["id"])
            for id in seguiments:
                all_seguiments[seguiments[id]['id']] = seguiments[id]
    return all_seguiments

def delete_document(docid):
    payload = {"key": os.environ["LILT_API_KEY"], "id": docid}
    res = requests.delete(lilt_api_url + "/documents", params=payload, verify=False)

def upload_document(filename, project_id):
    all_seguiments = get_all_seguiments_by_project(project_id)
    payload = {"key": os.environ["LILT_API_KEY"]}
    jsonData = {"name": filename, "project_id": project_id}
    headers = { "LILT-API": json.dumps(jsonData), "Content-Type": "application/octet-stream" }

    with open(filename, 'r') as fp:
        rawdata = fp.read()

    local_seguiments = json.loads(rawdata)

    new_seguiments = {}
    for localseguiment in local_seguiments:
        if localseguiment in all_seguiments:
            new_seguiments[localseguiment] = all_seguiments[localseguiment]['source']
        else:
            new_seguiments[localseguiment] = localseguiment

    res = requests.post(lilt_api_url + "/documents/files", params=payload, data=json.dumps(new_seguiments), headers=headers, verify=False)
    document_id = res.json()["id"]

    time.sleep(2)

    pretranslate_document(document_id)
    pretranslate_document(document_id)

    return document_id

def download_document(project_id):
    all_seguiments = get_all_seguiments_by_project(project_id)
    new_document = {}
    for id in all_seguiments:
        new_document[all_seguiments[id]['source']] = all_seguiments[id]['translation']
    return json.dumps(new_document, indent=2, sort_keys=True)

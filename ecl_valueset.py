"""
   Build a FHIR ValueSet from an ECL expression file and a matching FHIR template,
   then optionally post it to a FHIR endpoint.

   The template for ecl/<name>.ecl is fhir_templates/<name>.json; every occurrence
   of $expression in the template's string values is replaced by the ECL expression.
"""

import json
import logging
import os
from urllib.parse import unquote

import requests

logger = logging.getLogger(__name__)

PLACEHOLDER = "$expression"
FHIR_HEADERS = {'Accept': 'application/fhir+json', 'Content-Type': 'application/fhir+json'}


## read_ecl
#     Read an ECL file and return the expression as plain text.
#     URL-encoded expressions (e.g. copied from a $expand URL) are decoded.
def read_ecl(eclfile):
    with open(eclfile) as f:
        ecl = f.read()
    if '%' in ecl:
        ecl = unquote(ecl)
    return ecl.strip()


## template_for
#     Return the template path with the same base name as the ECL file
def template_for(eclfile, templates_path):
    name = os.path.splitext(os.path.basename(eclfile))[0]
    return os.path.join(templates_path, f'{name}.json')


## substitute
#     Recursively replace the placeholder in every string of a JSON structure.
#     Done on the parsed JSON (not the raw text) so quotes etc. in the ECL are escaped correctly.
def substitute(node, ecl):
    if isinstance(node, dict):
        return {k: substitute(v, ecl) for k, v in node.items()}
    if isinstance(node, list):
        return [substitute(v, ecl) for v in node]
    if isinstance(node, str):
        return node.replace(PLACEHOLDER, ecl)
    return node


def build_valueset(eclfile, template):
    """
    Build a ValueSet dict from the ECL file and template
    """
    with open(template) as f:
        tmpl = json.load(f)
    if PLACEHOLDER not in json.dumps(tmpl):
        raise ValueError(f'{template} does not contain {PLACEHOLDER}')
    return substitute(tmpl, read_ecl(eclfile))


def post_valueset(vs, endpoint):
    """
    Send the ValueSet to the endpoint: PUT ValueSet/{id} when the template has an id
    (create or update), otherwise POST ValueSet. Returns the requests response.
    """
    base = endpoint.rstrip('/')
    if vs.get('id'):
        response = requests.put(f"{base}/ValueSet/{vs['id']}", json=vs, headers=FHIR_HEADERS)
    else:
        response = requests.post(f"{base}/ValueSet", json=vs, headers=FHIR_HEADERS)
    if not response.ok:
        logger.error(f'{response.status_code} from {response.url}: {response.text}')
    return response


## Mainline
## Build a ValueSet for each ECL file, write it to outdir and post it to endpoint (if given)
def run_main(eclfiles, outdir, endpoint, templates_path):
    os.makedirs(outdir, exist_ok=True)
    for eclfile in eclfiles:
        template = template_for(eclfile, templates_path)
        if not os.path.exists(template):
            msg = f'No template {template} for {eclfile}, ...skipping'
            logger.error(msg)
            print('Error: ' + msg)
            continue
        vs = build_valueset(eclfile, template)
        name = vs.get('id') or os.path.splitext(os.path.basename(template))[0]
        outfile = os.path.join(outdir, f"ValueSet-{name}.json")
        with open(outfile, "w") as f:
            json.dump(vs, f, indent=2, ensure_ascii=False)
        msg = f'Built {outfile} from {eclfile} and {template}'
        if endpoint:
            response = post_valueset(vs, endpoint)
            msg += f', {endpoint} returned {response.status_code}'
        logger.info(msg)
        print(msg)

# make-vs

Builds FHIR ValueSets from SNOMED CT ECL expressions and, optionally, posts them to a FHIR terminology server.

For each ECL file `ecl/<name>.ecl`, the script loads the template `fhir_templates/<name>.json`, replaces every `$expression` in it with the ECL, writes the result to the output directory, and can then send it to a FHIR endpoint.

## Setup

Requires Python 3.12+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
# Build only; writes out/ValueSet-aucdi-substance-use-1.json
.venv/bin/python main.py -e ecl/aucdi-substance-use.ecl

# Build and post to the default endpoint (http://localhost:8080/fhir)
.venv/bin/python main.py -e ecl/aucdi-substance-use.ecl -p

# Build and post to a named endpoint
.venv/bin/python main.py -e ecl/aucdi-substance-use.ecl -p https://r4.ontoserver.csiro.au/fhir

# Build several ValueSets at once
.venv/bin/python main.py -e ecl/*.ecl
```

| Option | Default | Description |
| --- | --- | --- |
| `-e`, `--ecl` | *(required)* | One or more ECL files |
| `-t`, `--templates` | `fhir_templates` | Folder containing the templates |
| `-o`, `--outdir` | `out` | Folder for the generated ValueSet JSON |
| `-p`, `--publish` | not posted | FHIR endpoint to post to; `-p` on its own uses `http://localhost:8080/fhir` |

Each run writes a log to `logs/make-vs-<timestamp>.log`. Server errors are recorded there.

## Adding a ValueSet

1. Save the ECL expression as `ecl/<name>.ecl`. It can be plain ECL or URL-encoded, such as an expression copied from a `$expand` URL; URL-encoded files are decoded automatically.
2. Create `fhir_templates/<name>.json` with the same `<name>`. This is a complete ValueSet resource with `$expression` where the ECL should go, usually in a `constraint` filter:

   ```json
   "compose": {
     "include": [
       {
         "system": "http://snomed.info/sct",
         "filter": [
           { "property": "constraint", "op": "=", "value": "$expression" }
         ]
       }
     ]
   }
   ```

3. Run `main.py -e ecl/<name>.ecl`.

The script skips an ECL file that has no matching template, and it fails if the template does not contain `$expression`.

## Posting behaviour

- If the template has an `id`, the ValueSet is sent as `PUT <endpoint>/ValueSet/<id>`. This creates the ValueSet or **overwrites** the existing one with that id.
- If the template has no `id`, the ValueSet is sent as `POST <endpoint>/ValueSet`, and the server assigns an id.

The output file is named `ValueSet-<id>.json`, or `ValueSet-<name>.json` when the template has no `id`.

import argparse
import logging
import os
from datetime import datetime

import ecl_valueset


def main():
    parser = argparse.ArgumentParser()
    #endpoint_default="https://r4.ontoserver.csiro.au/fhir"
    endpoint_default="http://localhost:8080/fhir"
    logger = logging.getLogger(__name__)
    parser.add_argument("-e", "--ecl", nargs="+", required=True, help="ECL file(s); builds a ValueSet from the equivalently named template in --templates")
    parser.add_argument("-o", "--outdir", help="Output directory for generated resources", default="out")
    parser.add_argument("-t", "--templates", help="FHIR template directory", default="fhir_templates")
    parser.add_argument("-p", "--publish", nargs="?", const=endpoint_default, default="",
                        help=f"Post resources to this FHIR endpoint (default when flag given without a value: {endpoint_default})")

    args = parser.parse_args()
    now = datetime.now().astimezone() # current date and time
    ts = now.strftime("%Y%m%d-%H%M%S")
    FORMAT='%(asctime)s %(lineno)d : %(message)s'
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(format=FORMAT, filename=os.path.join('logs',f'make-vs-{ts}.log'),level=logging.INFO)
    logger.info('Started')
    ecl_valueset.run_main(args.ecl,args.outdir,args.publish,args.templates)
    logger.info("Finished")

if __name__ == '__main__':
    main()

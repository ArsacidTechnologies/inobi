from inobi.reports import route, config, error_codes as ec
from uuid import uuid4
import os
from flask import make_response, send_file
from inobi.reports.generator import xlsx
from inobi.utils.converter import converted
from inobi.exceptions import BaseInobiException
from flask_cors import cross_origin


@route('/v1', methods=['POST'])
@cross_origin()
@converted(rest_key='rest')
def make_report(rest: None):
    data = rest.json
    filename = '{}.xlsx'.format(uuid4())
    filename = os.path.join(config.FOLDER_DIRECTORY, filename)
    try:
        file = xlsx.make_report(data, filename)
    except KeyError as e:
        raise BaseInobiException("key error {}".format(e), ec.KEY_ERROR, 400)
    fn = os.path.basename(filename)
    r = make_response(send_file(file, as_attachment=True, attachment_filename=fn))
    r.headers['X-Filename'] = fn
    return r

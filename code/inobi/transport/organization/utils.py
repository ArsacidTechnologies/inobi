
import typing as T

from ..DataBase.classes import TransportOrganization
import inobi.mobile_app.db.user as user_db
from functools import wraps
from inobi.exceptions import BaseInobiException
from inobi.transport import error_codes as ec
from inobi.transport.organization.db.models import TransportOrganizations


def user_from_token(token_data: dict) -> user_db.User:
    return user_db.User.make_from_dict(token_data['user'])


def transport_organization_from_token(token_data: dict) -> T.Optional['TransportOrganization']:
    to_dict = token_data.get('transport_organization', None)
    if to_dict is None:
        return None
    return TransportOrganization(**{
            k: v
            for k, v in to_dict.items()
            if k in TransportOrganization._fields
        }, traccar_password=None)


from flask import jsonify, Response
from collections import OrderedDict
import xlsxwriter
import os


def save_to_xlsx(report, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    thead = workbook.add_format(
        {'bold': 1, 'border': 1, 'font_size': 12, 'font_color': 'white', 'align': 'center', 'bg_color': '#0088CC'})
    tbody = workbook.add_format({'border': 1, 'font_size': 11, 'align': 'center'})

    # period
    worksheet.write('C3', report['title'], bold)
    # table head
    thead_row = 4
    thead_col = 1

    for head in OrderedDict(sorted(report['data'][0].items(), key=lambda t: len(t[0]))):
        worksheet.write(thead_row, thead_col, head.replace('_', ' ').title(), thead)
        thead_col += 1

    # table body
    row = 5
    col = 1
    for item in report['data']:
        for value in OrderedDict(sorted(item.items(), key=lambda t: len(t[0]))).values():
            worksheet.write(row, col, value, tbody)
            col += 1
        row += 1
        col = 1
    # set colum size
    worksheet.set_column(
        'B:G',
        15
    )
    workbook.close()

    # # download file
    # file_name = os.path.join(OUTPUT_DIR, 'report.xlsx')
    # if not os.path.isfile(file_name):
    #     return jsonify({"message": "still processing"})
    # # read without gzip.open to keep it compressed
    # with open(file_name, 'rb') as f:
    #     resp = Response(f.read())
    # # set headers to tell encoding and to send as an attachment
    # resp.headers["Content-Encoding"] = 'xlsx'
    # resp.headers["Content-Disposition"] = "attachment; filename={0}".format('report.xlsx')
    # resp.headers["Content-type"] = "text/xlsx"
    return filename



from inspect import signature


def organization_required(*args, **kwargs):
    is_table = kwargs.get('is_table', False)
    token_data_key = kwargs.get('token_data_key', 'token_data')
    scopes_key = kwargs.get('scopes_key', 'scopes')

    def wow(f):
        params = signature(f).parameters
        requires_token_data = token_data_key in params
        requires_scopes = scopes_key in params

        def wrapper(*fargs, token_data=None, scopes=None, **fkwargs):
            organization = token_data.get('transport_organization')
            if not organization:
                raise BaseInobiException("Organization Data Is Missing", http_code=403, code=ec.ACCESS_DENIED)
            organization_id = organization.get('id')
            if not organization_id:
                raise BaseInobiException("Organization id Is Missing", http_code=403, code=ec.ACCESS_DENIED)
            if not is_table:
                r_organization = organization_id
            else:
                organization = TransportOrganizations.query.get(organization_id)
                if not organization:
                    raise BaseInobiException("Organization not found", http_code=403, code=ec.ACCESS_DENIED)
                r_organization = organization

            d = {"organization": r_organization}
            if requires_token_data:
                d['token_data'] = token_data
            if requires_scopes:
                d['scopes'] = scopes
            return f(*fargs, **fkwargs, **d)
        wrapper.__name__ = f.__name__
        return wrapper
    return wow

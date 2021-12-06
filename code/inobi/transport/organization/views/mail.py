from ...organization import bp
from inobi.utils import http_ok, http_err
from inobi.utils.converter import converted
from inobi.mobile_app.utils import send_email
from flask_cors import cross_origin
from inobi.security import secured
import os
from inobi.transport.configs import TRANSPORT_REPORT_DIRECTORY, Attachment
from threading import Thread
from uuid import uuid4
from inobi.transport.organization.utils import save_to_xlsx


@bp.route('/v1/mail', methods=['POST'])
@cross_origin()
@secured('transport_viewer')
@converted(rest_key='kwargs')
def mail(to_address, subject: str, message: str, attachment=None,
         attachment_type: str=None, from_address: str=None, kwargs=None):
    if attachment_type:
        if attachment_type == Attachment.REPORT:
            if not attachment:
                if not kwargs.get('report'):
                    return http_err('attachment or report required', 400)
                report = kwargs['report']
                if not report.get('title'):
                    return http_err('report title is missing', 400)
                if not report.get('data'):
                    return http_err('report data is missing', 400)
                if not isinstance(report['data'], list):
                    return http_err('report data must be list', 400)

                for item in report['data']:
                    if not isinstance(item, dict):
                        return http_err('report data must be array of dict', 400)
                filename = '{}.xlsx'.format(uuid4())
                filename = os.path.join(TRANSPORT_REPORT_DIRECTORY, filename)
                file = save_to_xlsx(report, filename)
                attachment = [file]
            directory = TRANSPORT_REPORT_DIRECTORY

        else:
            return http_err('unknown attachment_type', 400, available=[Attachment.REPORT])
        attachment = [attachment] if not isinstance(attachment, list) else attachment
        for att in attachment:
            if not os.path.exists(os.path.join(directory, att)):
                return http_err('not found {}'.format(att), 400)
        attachment = [os.path.join(directory, att) for att in attachment]
    params = dict(to_address=to_address,
                  subject=subject,
                  message=message,
                  from_address=from_address,
                  files=attachment)
    Thread(target=send_email, kwargs=params, daemon=True).start()
    return http_ok()

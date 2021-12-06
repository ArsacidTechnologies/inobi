import xlsxwriter


def make_report(reports, filename):
    file_name = filename
    workbook = xlsxwriter.Workbook(file_name)
    # Value of table key is array of tables, they should be written separately in different sheets
    for report in reports['tables']:
        # Total for specific columns should be written in a dynamic way in last cell under given column
        # Need to create a dict to store the index of column, if to imagine as excel table
        position = dict()
        worksheet = workbook.add_worksheet()

        title_fmt = workbook.add_format({"bold": True, "font_size": 14})
        total_fmt = workbook.add_format({"bold": True, "font_size": 12, "align": "center", "border": 1})
        bold = workbook.add_format({'bold': True})
        thead = workbook.add_format(
            {'bold': 1, 'border': 1, 'font_size': 12, 'font_color': 'white', 'align': 'center', 'bg_color': '#0088CC'})
        tbody = workbook.add_format({'border': 1, 'font_size': 11, 'align': 'center'})
        worksheet.merge_range('B2:G2', report['title'], title_fmt)

        description_row = 4
        # for method merge_range need to pass the argument in format (example:"C3:J3")
        # to make it in a dynamic way need to increment the row value and build a new string
        for des in report['description']:
            row_range = 'B' + str(description_row) + ':' + 'G' + str(description_row)
            worksheet.merge_range(row_range, des['key'] + ': ' + des['value'], bold)
            description_row += 1

        thead_row = description_row + 1
        thead_col = 1

        for column in report['columns']:
            worksheet.write(thead_row, thead_col, column['label'], thead)
            # As mentioned need to store index of column to write the total in cell under right column
            position[column['key']] = thead_col
            thead_col += 1
        row = thead_row + 1

        for i in range(len(report['data'])):
            col = 1
            for key in report['columns']:
                if report['data'][i].get(key['key']) is None or report['data'][i][key['key']] == '':
                    worksheet.write(row, col, '---', tbody)
                else:
                    worksheet.write(row, col, report['data'][i][key['key']], tbody)

                col += 1
            row += 1

        # Adds one formated row to the table, since total might be written on last row
        if report.get('total'):
            col = 1
            for i in range(len(report['columns'])):
                worksheet.write(row, col, '', tbody)
                col += 1
            
        # Writes total for given columns
        try:
            for column, total in report['total'].items():
                if position.get(column) is not None and total != '':
                    worksheet.write(row, position[column], total, total_fmt)
        except KeyError:
            pass
    
        worksheet.set_column(
            'B:Z',
            22
        )

    workbook.close()

    return filename
import xlrd
import codecs

NEW_LINE = '\n'

data_list = []

def read(path, x1, y1, x2, y2):
    workbook = xlrd.open_workbook(path)
    # worksheet = workbook.sheet_by_index(0)
    sheets = workbook.sheet_names()
    worksheet = workbook.sheet_by_name(sheets[0])
    for i in range(0, worksheet.nrows):
        # row = worksheet.row(i)
        # print(worksheet.cell_value(i, 0))
        data_list.append(worksheet.cell_value(i, 0))

def append_in_file(path):
    fw = codecs.open(path, 'a', encoding='utf-8')
    for data in data_list:
        fw.write(data + NEW_LINE)
    fw.close()
    print('write completed.')


if __name__ == '__main__':
    read('../data/11111111.xlsx', 1, 253, 2, 253)
    append_in_file('../data/corpus/questions.txt')

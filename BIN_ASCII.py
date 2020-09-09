

# *********************************************************************
def Convert_Str_to_Bytearray(text_in):
    '''
    :param text_in:
    :param bytearray_out:
    :return:
    '''
    if isinstance(text_in, str):
        bytearray_out = bytearray(b'')
        for data in text_in:
            bytearray_out += ord(data).to_bytes(1, 'big')
        return bytearray_out
    else:
        return None

# *********************************************************************
def Convert_HexStr_to_Bytearray(text_in):
    '''
    :param text_in:
    :param bytearray_out:
    :return:
    '''
    if isinstance(text_in, str):
        bytearray_out = bytearray(b'')
        i = 0
        strLength = len(text_in)
        while i < strLength:
            convStr = text_in[i:i+2]
            bytearray_out += int(convStr, 16).to_bytes(1, 'big')
            i+=2
        return bytearray_out
    else:
        return None

def Convert_ArrBite_to_ArrChar(data):
    '''
    #*********************************************************************
    # извлечение номера в формате str из данных в формате byte
    # [data] - данные в формате byte
    #*********************************************************************
    '''
    text = ''
    lenData = len(data)
    for i in range(lenData):
        text += chr(data[i])
    return text

def Convert_ArrBite_to_ArrCharHex(data):
    '''
    #*********************************************************************
    # конвертация символов bite в последовательность символов Hex
    # [data] - данные в формате byte
    #*********************************************************************
    '''
    text = ''
    lenData = len(data)
    try:
        for i in range(lenData):
            if int(data[i]) > 0x0f:
                text += hex(data[i])[2:]
            else:
                text += '0' + hex(data[i])[2:]
    except:
        return ''
    return text

#*********************************************************************
def Del_Spaces(data):
    '''
    удаление пробелов в строковом списке
    :param data: строковый список для обработки
    :return: data_out - искходый список но без пробелов
    '''
    data_out = []
    for row in data:
        row_out = []
        for pos in row:
            if isinstance(pos, str) and pos != '':
                while pos[-1] == ' ':
                    pos = pos[:-1]
                    if len(pos) == 0:
                        break
            row_out.append(pos)
        data_out.append(row_out)
    return data_out

#*********************************************************************
def Byte_to_Bytearray(RX_Data):
    '''
    #перевод данных из byte в bytearray
    :param RX_Data:
    :return:
    '''
    #переводим принятые данные в bytearray для удобства дальнейшей работы с ними
    RX_Data_return = bytearray(len(RX_Data))
    for i in range(len(RX_Data)):
        RX_Data_return[i] = RX_Data[i]
    return RX_Data_return
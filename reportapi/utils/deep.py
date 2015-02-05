# -*- coding: utf-8 -*-
#
#  reportapi/utils/deep.py
#  
#  Copyright 2014 Grigoriy Kramarenko <root@rosix.ru>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

def to_dict(dictionary, field, value, append_to_list=False):
    """
    Рекурсивное обновление поля словаря. Ключ значения может выглядеть как:
    'field'
    или
    'field1.field2.field3'
    или
    ['field1', 'field2', ...]

    Заметьте, что (по умолчанию) списки поддерживаются только в
    качестве готовых значений! Если нужно добавить в список, то
    передавайте параметр `append_to_list=True`.
    Тогда, если такого списка нет, то он создастся с переданным
    значением внутри, если же есть и это действительно список,
    то добавит в него. Если же назначение не список, то вызовет ошибку.

    """
    D = dictionary

    if not isinstance(D, dict):
        D = {}

    if not isinstance(field, (list, tuple)):
        field = field.split('.')

    d = D
    length = len(field)
    dest = length-1
    for i in range(0, length):
        key = field[i]
        if not d.has_key(key):
            if i == dest:
                if append_to_list:
                    d[key] = [value]
                else:
                    d[key] = value
            else:
                d[key] = {}
                d = d[key]
        elif i == dest:
            if append_to_list:
                d[key].append(value)
            else:
                d[key] = value
        else:
            d = d[key]

    return D


def from_dict(dictionary, field, default=None, update=True, delete=False):
    """
    Рекурсивное получение поля словаря. Ключ значения может выглядеть как:
    'field'
    или
    'field1.field2.field3'
    или
    ['field1', 'field2', ...]
    
    Устанавливает значение по-умолчанию, если ничего не найдено и
    разрешено обновление.
    Если задано удаление, то удаляет этот ключ.
    """
    D = dictionary

    if not isinstance(D, dict):
        D = {}

    if not isinstance(field, (list, tuple)):
        field = field.split('.')

    d = D
    value = default
    length = len(field)
    dest = length-1
    for i in range(0, length):
        key = field[i]
        if not d.has_key(key):
            if not update or delete:
                return value
            elif i == dest:
                d[key] = value
            else:
                d[key] = {}
                d = d[key]
        elif i == dest:
            if delete:
                return d.pop(key)
            else:
                value = d[key] 
        else:
            d = d[key]

    return value

